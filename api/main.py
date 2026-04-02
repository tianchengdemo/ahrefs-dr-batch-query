# -*- coding: utf-8 -*-
"""
Ahrefs DR query API.
"""

import re
import queue
import threading
import time
import uuid
import os
from datetime import datetime
from typing import Dict, List, Optional

import uvicorn
import config as app_config
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

from ahrefs import AhrefsClient
from config import (
    AHREFS_COOKIE,
    API_AUTH_ENABLED,
    API_KEYS,
    APP_ID,
    APP_SECRET,
    CONTAINER_CODE,
    COOKIE_CACHE_TTL_MINUTES,
    DEFAULT_COUNTRY,
    HUBSTUDIO_API_BASE,
    HUBSTUDIO_CDP_HOST,
    RESULT_CACHE_DB_PATH,
    RESULT_CACHE_ENABLED,
    RESULT_CACHE_TTL_DAYS,
    SOCKS5_PROXY,
)
from hubstudio import HubStudioClient
from result_cache import DomainResultCache, GLOBAL_CACHE_SCOPE


app = FastAPI(
    title="Ahrefs DR Batch Query API",
    description="Query Ahrefs DR and AR with HubStudio-backed auth and local caching.",
    version="2.4.1",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REDIS_ENABLED = os.getenv(
    "REDIS_ENABLED",
    str(getattr(app_config, "REDIS_ENABLED", False)),
).strip().lower() in {"1", "true", "yes", "on"}
REDIS_URL = os.getenv(
    "REDIS_URL",
    getattr(app_config, "REDIS_URL", ""),
).strip()
REDIS_CACHE_TTL_SECONDS = int(
    os.getenv(
        "REDIS_CACHE_TTL_SECONDS",
        str(getattr(app_config, "REDIS_CACHE_TTL_SECONDS", 21600)),
    )
)
REDIS_KEY_PREFIX = os.getenv(
    "REDIS_KEY_PREFIX",
    getattr(app_config, "REDIS_KEY_PREFIX", "ahrefs:domain-cache:"),
).strip()
API_MAX_BATCH_DOMAINS = max(
    1,
    int(
        os.getenv(
            "API_MAX_BATCH_DOMAINS",
            str(getattr(app_config, "API_MAX_BATCH_DOMAINS", 20)),
        )
    ),
)
API_MAX_CONCURRENT_LIVE_TASKS = max(
    1,
    int(
        os.getenv(
            "API_MAX_CONCURRENT_LIVE_TASKS",
            str(getattr(app_config, "API_MAX_CONCURRENT_LIVE_TASKS", 2)),
        )
    ),
)
API_MAX_QUEUED_LIVE_TASKS = max(
    1,
    int(
        os.getenv(
            "API_MAX_QUEUED_LIVE_TASKS",
            str(getattr(app_config, "API_MAX_QUEUED_LIVE_TASKS", 20)),
        )
    ),
)
API_TASK_TIMEOUT_SECONDS = max(
    10,
    int(
        os.getenv(
            "API_TASK_TIMEOUT_SECONDS",
            str(getattr(app_config, "API_TASK_TIMEOUT_SECONDS", 180)),
        )
    ),
)

tasks_storage: Dict[str, dict] = {}
result_cache = DomainResultCache(
    db_path=RESULT_CACHE_DB_PATH,
    ttl_days=RESULT_CACHE_TTL_DAYS,
    enabled=RESULT_CACHE_ENABLED,
    redis_enabled=REDIS_ENABLED,
    redis_url=REDIS_URL,
    redis_ttl_seconds=REDIS_CACHE_TTL_SECONDS,
    redis_key_prefix=REDIS_KEY_PREFIX,
)

_cookie_lock = threading.Lock()
_cookie_cache = {
    "cookie": None,
    "proxy_url": SOCKS5_PROXY,
    "expires_at": 0.0,
}
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
configured_api_keys = {key.strip() for key in API_KEYS if key and key.strip()}
_live_task_slots = threading.BoundedSemaphore(API_MAX_CONCURRENT_LIVE_TASKS)
_live_task_queue: "queue.Queue[tuple[str, List[str], str]]" = queue.Queue(
    maxsize=API_MAX_QUEUED_LIVE_TASKS
)
_live_task_workers_started = False
_live_task_workers_lock = threading.Lock()
_live_task_metrics_lock = threading.Lock()
_live_task_active = 0


class QueryRequest(BaseModel):
    domain: str = Field(..., description="Domain", example="example.com")
    country: Optional[str] = Field(
        DEFAULT_COUNTRY,
        description="Reserved for future country-specific metrics. DR/AR endpoints return global domain values.",
        example="us",
    )
    async_mode: bool = Field(
        False,
        description="When true, create a background task and return pending instead of waiting for the live result.",
        example=False,
    )


class BatchQueryRequest(BaseModel):
    domains: List[str] = Field(..., description="Domain list", example=["example.com", "google.com"])
    country: Optional[str] = Field(
        DEFAULT_COUNTRY,
        description="Reserved for future country-specific metrics. DR/AR endpoints return global domain values.",
        example="us",
    )


class TaskResponse(BaseModel):
    task_id: str = Field(..., description="Task ID")
    status: str = Field(..., description="Task status")
    message: str = Field(..., description="Task message")
    results: Optional[List["QueryResult"]] = Field(None, description="Completed results when immediately available")
    source: Optional[str] = Field(None, description="Result source: cache, live, or mixed")
    cached_domains: int = Field(0, description="How many domains were served from cache")
    live_domains: int = Field(0, description="How many domains required live querying")


class QueryResult(BaseModel):
    domain: str
    domain_rating: Optional[float]
    ahrefs_rank: Optional[int]
    dr_delta: Optional[float] = None
    ar_delta: Optional[int] = None
    error: Optional[str] = None


class TaskResult(BaseModel):
    task_id: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    results: Optional[List[QueryResult]] = None
    error: Optional[str] = None
    source: Optional[str] = None
    cached_domains: int = 0
    live_domains: int = 0


def verify_api_key(x_api_key: Optional[str] = Depends(api_key_header)) -> None:
    if not API_AUTH_ENABLED:
        return

    if not configured_api_keys:
        raise HTTPException(status_code=500, detail="API auth is enabled but API_KEYS is empty")

    if x_api_key and x_api_key in configured_api_keys:
        return

    raise HTTPException(status_code=401, detail="Invalid or missing API key")


def normalize_domain(domain: str) -> str:
    value = domain.strip().lower()
    value = re.sub(r"^https?://", "", value)
    value = value.rstrip("/")
    value = re.sub(r"^www\.", "", value)
    return value


def normalize_country(country: Optional[str]) -> str:
    return (country or DEFAULT_COUNTRY).strip().lower()


def get_metrics_query_country(_: Optional[str] = None) -> str:
    # Domain Rating and Ahrefs Rank are domain-level metrics.
    # Keep the upstream query country fixed so results and cache scope stay global.
    return DEFAULT_COUNTRY


def get_metrics_cache_scope() -> str:
    return GLOBAL_CACHE_SCOPE


def should_cache_result(result: dict) -> bool:
    if result.get("error"):
        return False
    return result.get("domain_rating") is not None or result.get("ahrefs_rank") is not None


def should_refresh_cookie(results: List[dict]) -> bool:
    for result in results:
        if result is None:
            continue
        error = str(result.get("error", "")).lower()
        if "403" in error or "forbidden" in error:
            return True
    return False


def detect_result_source(cached_domains: int, live_domains: int) -> str:
    if live_domains == 0:
        return "cache"
    if cached_domains == 0:
        return "live"
    return "mixed"


def build_error_result(domain: str, error: str) -> dict:
    return {
        "domain": domain,
        "domain_rating": None,
        "ahrefs_rank": None,
        "dr_delta": None,
        "ar_delta": None,
        "error": error,
    }


def build_task_record(task_id: str, domains: List[str], country: str) -> dict:
    return {
        "task_id": task_id,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "domains": domains,
        "country": country,
        "source": None,
        "cached_domains": 0,
        "live_domains": len(domains),
    }


def get_live_task_stats() -> dict:
    with _live_task_metrics_lock:
        active = _live_task_active
    return {
        "active": active,
        "queued": _live_task_queue.qsize(),
        "max_concurrent": API_MAX_CONCURRENT_LIVE_TASKS,
        "max_queued": API_MAX_QUEUED_LIVE_TASKS,
    }


def _set_task_completion_event(task_id: str) -> None:
    task = tasks_storage.get(task_id)
    if not task:
        return
    completion_event = task.get("_completion_event")
    if completion_event:
        completion_event.set()


def _mark_live_task_started(task_id: str) -> None:
    with _live_task_metrics_lock:
        global _live_task_active
        _live_task_active += 1
    task = tasks_storage.get(task_id)
    if task:
        task["status"] = "processing"
        task["started_at"] = datetime.now().isoformat()


def _mark_live_task_finished(task_id: str) -> None:
    with _live_task_metrics_lock:
        global _live_task_active
        _live_task_active = max(0, _live_task_active - 1)
    _set_task_completion_event(task_id)


def _live_task_worker() -> None:
    while True:
        task_id, domains, country = _live_task_queue.get()
        _live_task_slots.acquire()
        try:
            _mark_live_task_started(task_id)
            process_query_task(task_id, domains, country)
        finally:
            _mark_live_task_finished(task_id)
            _live_task_slots.release()
            _live_task_queue.task_done()


def ensure_live_task_workers_started() -> None:
    global _live_task_workers_started
    if _live_task_workers_started:
        return
    with _live_task_workers_lock:
        if _live_task_workers_started:
            return
        for index in range(API_MAX_CONCURRENT_LIVE_TASKS):
            worker = threading.Thread(
                target=_live_task_worker,
                name=f"live-query-worker-{index + 1}",
                daemon=True,
            )
            worker.start()
        _live_task_workers_started = True


def enqueue_live_task(task_id: str, domains: List[str], country: str) -> None:
    ensure_live_task_workers_started()
    task = tasks_storage[task_id]
    task["_completion_event"] = threading.Event()
    task["queued_at"] = datetime.now().isoformat()
    try:
        _live_task_queue.put_nowait((task_id, domains, country))
    except queue.Full as exc:
        task.pop("_completion_event", None)
        task["status"] = "failed"
        task["error"] = (
            f"Live query queue is full ({API_MAX_QUEUED_LIVE_TASKS}). "
            "Retry later or reduce concurrency."
        )
        task["completed_at"] = datetime.now().isoformat()
        raise HTTPException(
            status_code=429,
            detail=(
                f"Live query queue is full ({API_MAX_QUEUED_LIVE_TASKS}). "
                "Retry later or use a smaller request rate."
            ),
        ) from exc


def run_live_task_now(task_id: str, domains: List[str], country: str) -> bool:
    if _live_task_queue.qsize() > 0:
        return False
    if not _live_task_slots.acquire(blocking=False):
        return False
    try:
        _mark_live_task_started(task_id)
        process_query_task(task_id, domains, country)
        return True
    finally:
        _mark_live_task_finished(task_id)
        _live_task_slots.release()


def invalidate_cookie_cache() -> None:
    with _cookie_lock:
        _cookie_cache["cookie"] = None
        _cookie_cache["expires_at"] = 0.0
        _cookie_cache["proxy_url"] = SOCKS5_PROXY


def _load_cookie_from_hubstudio() -> tuple[str, Optional[str]]:
    cookie = None
    proxy_url = SOCKS5_PROXY
    hub = HubStudioClient(
        api_base=HUBSTUDIO_API_BASE,
        app_id=APP_ID,
        app_secret=APP_SECRET,
        cdp_host=HUBSTUDIO_CDP_HOST,
    )
    browser_started = False

    try:
        browser_info = hub.start_browser(
            CONTAINER_CODE,
            enable_cdp=True,
            open_url="https://app.ahrefs.com",
        )
        browser_started = True
        debugging_port = browser_info.get("debuggingPort")

        if debugging_port:
            time.sleep(5)
            cookies = hub.get_cookies_via_cdp(debugging_port, "ahrefs.com")
            if cookies:
                cookie = hub.build_cookie_header(cookies)
            else:
                cookies = hub.export_cookies(CONTAINER_CODE)
                if cookies:
                    cookie = hub.build_cookie_header(cookies)

        if not proxy_url:
            proxy_url = hub.get_proxy_for_env(CONTAINER_CODE)
    finally:
        if browser_started:
            try:
                hub.stop_browser(CONTAINER_CODE)
            except Exception:
                pass

    return cookie or "", proxy_url


def get_ahrefs_client(force_refresh: bool = False) -> AhrefsClient:
    now_ts = time.time()

    with _cookie_lock:
        if (
            not force_refresh
            and _cookie_cache["cookie"]
            and now_ts < _cookie_cache["expires_at"]
        ):
            return AhrefsClient(
                cookie_header=_cookie_cache["cookie"],
                proxy_url=_cookie_cache["proxy_url"],
            )

    cookie = ""
    proxy_url = SOCKS5_PROXY

    if CONTAINER_CODE and APP_ID and APP_SECRET:
        try:
            cookie, proxy_url = _load_cookie_from_hubstudio()
        except Exception as exc:
            print(f"[API] Failed to refresh cookie from HubStudio: {exc}")

    if not cookie:
        cookie = AHREFS_COOKIE

    if not cookie:
        raise HTTPException(status_code=500, detail="Cookie is not configured")

    expires_at = now_ts + max(COOKIE_CACHE_TTL_MINUTES, 0) * 60
    with _cookie_lock:
        _cookie_cache["cookie"] = cookie
        _cookie_cache["proxy_url"] = proxy_url
        _cookie_cache["expires_at"] = expires_at

    return AhrefsClient(cookie_header=cookie, proxy_url=proxy_url)


def fetch_fresh_results(
    domains: List[str],
    country: str,
    force_refresh: bool = False,
    deadline_ts: Optional[float] = None,
) -> List[dict]:
    client = get_ahrefs_client(force_refresh=force_refresh)
    results = client.batch_get_domain_rating(domains, country=country, deadline_ts=deadline_ts)

    if should_refresh_cookie(results) and not force_refresh:
        invalidate_cookie_cache()
        client = get_ahrefs_client(force_refresh=True)
        results = client.batch_get_domain_rating(domains, country=country, deadline_ts=deadline_ts)

    return results


def get_cached_domain_metrics(domain: str) -> Optional[dict]:
    cache_scope = get_metrics_cache_scope()
    cached_result = result_cache.get(domain, cache_scope)
    if cached_result:
        return cached_result

    legacy_result = result_cache.get_any_country(domain)
    if legacy_result:
        result_cache.set(domain, cache_scope, legacy_result)
        return result_cache.get(domain, cache_scope) or legacy_result

    return None


def query_domains_with_cache(
    domains: List[str],
    country: str,
    deadline_ts: Optional[float] = None,
) -> dict:
    metrics_country = get_metrics_query_country(country)
    normalized_domains = []
    for domain in domains:
        normalized_domain = normalize_domain(domain)
        if normalized_domain:
            normalized_domains.append(normalized_domain)

    result_cache.prune_expired()

    ordered_results: List[Optional[dict]] = [None] * len(normalized_domains)
    missing_domains: List[str] = []
    missing_indexes: List[int] = []
    cached_domains = 0

    for index, domain in enumerate(normalized_domains):
        cached_result = get_cached_domain_metrics(domain)
        if cached_result:
            ordered_results[index] = cached_result
            cached_domains += 1
            continue

        missing_domains.append(domain)
        missing_indexes.append(index)

    if missing_domains:
        fresh_results = fetch_fresh_results(
            missing_domains,
            metrics_country,
            deadline_ts=deadline_ts,
        )
        for index, requested_domain, result in zip(missing_indexes, missing_domains, fresh_results):
            if result is None:
                continue
            normalized_result_domain = normalize_domain(result.get("domain", requested_domain))
            result["domain"] = normalized_result_domain
            ordered_results[index] = result
            if should_cache_result(result):
                result_cache.set(normalized_result_domain, get_metrics_cache_scope(), result)

        for index, requested_domain in zip(missing_indexes, missing_domains):
            if ordered_results[index] is None:
                ordered_results[index] = build_error_result(
                    requested_domain,
                    "Upstream query returned no result",
                )

    live_domains = len(missing_domains)
    return {
        "results": [result for result in ordered_results if result is not None],
        "cached_domains": cached_domains,
        "live_domains": live_domains,
        "source": detect_result_source(cached_domains, live_domains),
    }


def process_query_task(task_id: str, domains: List[str], country: str) -> None:
    try:
        deadline_ts = time.monotonic() + API_TASK_TIMEOUT_SECONDS
        query_output = query_domains_with_cache(domains, country, deadline_ts=deadline_ts)
        tasks_storage[task_id]["status"] = "completed"
        tasks_storage[task_id]["completed_at"] = datetime.now().isoformat()
        tasks_storage[task_id]["results"] = query_output["results"]
        tasks_storage[task_id]["source"] = query_output["source"]
        tasks_storage[task_id]["cached_domains"] = query_output["cached_domains"]
        tasks_storage[task_id]["live_domains"] = query_output["live_domains"]
    except Exception as exc:
        tasks_storage[task_id]["status"] = "failed"
        tasks_storage[task_id]["error"] = str(exc)
        tasks_storage[task_id]["completed_at"] = datetime.now().isoformat()


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "Ahrefs DR Batch Query API",
        "version": "2.4.1",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "result_cache_enabled": RESULT_CACHE_ENABLED,
        "result_cache_ttl_days": RESULT_CACHE_TTL_DAYS,
        "cookie_cache_ttl_minutes": COOKIE_CACHE_TTL_MINUTES,
        "redis_enabled": REDIS_ENABLED and bool(REDIS_URL),
        "redis_cache_ttl_seconds": REDIS_CACHE_TTL_SECONDS,
        "api_max_batch_domains": API_MAX_BATCH_DOMAINS,
        "api_task_timeout_seconds": API_TASK_TIMEOUT_SECONDS,
        "live_task_limits": get_live_task_stats(),
    }


@app.post("/api/query", response_model=TaskResponse, tags=["Query"], dependencies=[Depends(verify_api_key)])
async def query_domain(request: QueryRequest, background_tasks: BackgroundTasks):
    domain = normalize_domain(request.domain)
    requested_country = normalize_country(request.country)
    task_id = str(uuid.uuid4())

    tasks_storage[task_id] = build_task_record(task_id, [domain], requested_country)

    cached_result = get_cached_domain_metrics(domain)
    if cached_result:
        tasks_storage[task_id]["status"] = "completed"
        tasks_storage[task_id]["completed_at"] = datetime.now().isoformat()
        tasks_storage[task_id]["results"] = [cached_result]
        tasks_storage[task_id]["source"] = "cache"
        tasks_storage[task_id]["cached_domains"] = 1
        tasks_storage[task_id]["live_domains"] = 0
        return TaskResponse(
            task_id=task_id,
            status="completed",
            message="Result returned from cache",
            results=[cached_result],
            source="cache",
            cached_domains=1,
            live_domains=0,
        )

    if not request.async_mode:
        if not run_live_task_now(task_id, [domain], requested_country):
            tasks_storage.pop(task_id, None)
            raise HTTPException(
                status_code=429,
                detail=(
                    "Live query workers are busy. Retry later or call "
                    "/api/query with async_mode=true."
                ),
            )
        task = tasks_storage[task_id]
        if task["status"] == "failed":
            raise HTTPException(status_code=502, detail=task.get("error", "Query failed"))

        return TaskResponse(
            task_id=task_id,
            status=task["status"],
            message="Result fetched live",
            results=task.get("results"),
            source=task.get("source"),
            cached_domains=task.get("cached_domains", 0),
            live_domains=task.get("live_domains", 0),
        )

    try:
        enqueue_live_task(task_id, [domain], requested_country)
    except HTTPException:
        tasks_storage.pop(task_id, None)
        raise

    return TaskResponse(
        task_id=task_id,
        status="pending",
        message="Task created and processing",
        source="live",
        cached_domains=0,
        live_domains=1,
    )


@app.post("/api/batch", response_model=TaskResponse, tags=["Query"], dependencies=[Depends(verify_api_key)])
async def batch_query(request: BatchQueryRequest, background_tasks: BackgroundTasks):
    domains = []
    for domain in request.domains:
        normalized_domain = normalize_domain(domain)
        if normalized_domain:
            domains.append(normalized_domain)
    if not domains:
        raise HTTPException(status_code=400, detail="At least one valid domain is required")
    if len(domains) > API_MAX_BATCH_DOMAINS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Batch query supports at most {API_MAX_BATCH_DOMAINS} domains per request"
            ),
        )
    requested_country = normalize_country(request.country)
    task_id = str(uuid.uuid4())

    tasks_storage[task_id] = build_task_record(task_id, domains, requested_country)

    cached_results: List[Optional[dict]] = []
    all_cached = True
    for domain in domains:
        cached_result = get_cached_domain_metrics(domain)
        cached_results.append(cached_result)
        if not cached_result:
            all_cached = False

    if all_cached and domains:
        tasks_storage[task_id]["status"] = "completed"
        tasks_storage[task_id]["completed_at"] = datetime.now().isoformat()
        tasks_storage[task_id]["results"] = [result for result in cached_results if result]
        tasks_storage[task_id]["source"] = "cache"
        tasks_storage[task_id]["cached_domains"] = len(domains)
        tasks_storage[task_id]["live_domains"] = 0
        return TaskResponse(
            task_id=task_id,
            status="completed",
            message=f"All {len(domains)} results returned from cache",
            results=[result for result in cached_results if result],
            source="cache",
            cached_domains=len(domains),
            live_domains=0,
        )

    cached_domains = sum(1 for result in cached_results if result)
    live_domains = len(domains) - cached_domains
    tasks_storage[task_id]["cached_domains"] = cached_domains
    tasks_storage[task_id]["live_domains"] = live_domains
    tasks_storage[task_id]["source"] = detect_result_source(cached_domains, live_domains)

    try:
        enqueue_live_task(task_id, domains, requested_country)
    except HTTPException:
        tasks_storage.pop(task_id, None)
        raise

    return TaskResponse(
        task_id=task_id,
        status="pending",
        message=f"Task created and processing {len(domains)} domains",
        source=detect_result_source(cached_domains, live_domains),
        cached_domains=cached_domains,
        live_domains=live_domains,
    )


@app.get("/api/result/{task_id}", response_model=TaskResult, tags=["Query"], dependencies=[Depends(verify_api_key)])
async def get_result(task_id: str):
    if task_id not in tasks_storage:
        raise HTTPException(status_code=404, detail="Task not found")

    task = tasks_storage[task_id]
    return TaskResult(
        task_id=task["task_id"],
        status=task["status"],
        created_at=task["created_at"],
        completed_at=task.get("completed_at"),
        results=task.get("results"),
        error=task.get("error"),
        source=task.get("source"),
        cached_domains=task.get("cached_domains", 0),
        live_domains=task.get("live_domains", 0),
    )


@app.get("/api/tasks", tags=["Query"], dependencies=[Depends(verify_api_key)])
async def list_tasks():
    return {
        "total": len(tasks_storage),
        "live_task_limits": get_live_task_stats(),
        "tasks": [
            {
                "task_id": task["task_id"],
                "status": task["status"],
                "created_at": task["created_at"],
                "domains_count": len(task["domains"]),
            }
            for task in tasks_storage.values()
        ],
    }


if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
