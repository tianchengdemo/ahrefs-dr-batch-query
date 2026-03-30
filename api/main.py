# -*- coding: utf-8 -*-
"""
Ahrefs DR query API.
"""

import re
import threading
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ahrefs import AhrefsClient
from config import (
    AHREFS_COOKIE,
    APP_ID,
    APP_SECRET,
    CONTAINER_CODE,
    COOKIE_CACHE_TTL_MINUTES,
    DEFAULT_COUNTRY,
    HUBSTUDIO_API_BASE,
    RESULT_CACHE_DB_PATH,
    RESULT_CACHE_ENABLED,
    RESULT_CACHE_TTL_DAYS,
    SOCKS5_PROXY,
)
from hubstudio import HubStudioClient
from result_cache import DomainResultCache


app = FastAPI(
    title="Ahrefs DR Batch Query API",
    description="Query Ahrefs DR and AR with HubStudio-backed auth and local caching.",
    version="2.2.0",
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

tasks_storage: Dict[str, dict] = {}
result_cache = DomainResultCache(
    db_path=RESULT_CACHE_DB_PATH,
    ttl_days=RESULT_CACHE_TTL_DAYS,
    enabled=RESULT_CACHE_ENABLED,
)

_cookie_lock = threading.Lock()
_cookie_cache = {
    "cookie": None,
    "proxy_url": SOCKS5_PROXY,
    "expires_at": 0.0,
}


class QueryRequest(BaseModel):
    domain: str = Field(..., description="Domain", example="example.com")
    country: Optional[str] = Field(DEFAULT_COUNTRY, description="Country code", example="us")


class BatchQueryRequest(BaseModel):
    domains: List[str] = Field(..., description="Domain list", example=["example.com", "google.com"])
    country: Optional[str] = Field(DEFAULT_COUNTRY, description="Country code", example="us")


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


def normalize_domain(domain: str) -> str:
    value = domain.strip().lower()
    value = re.sub(r"^https?://", "", value)
    value = value.rstrip("/")
    value = re.sub(r"^www\.", "", value)
    return value


def normalize_country(country: Optional[str]) -> str:
    return (country or DEFAULT_COUNTRY).strip().lower()


def should_cache_result(result: dict) -> bool:
    if result.get("error"):
        return False
    return result.get("domain_rating") is not None or result.get("ahrefs_rank") is not None


def should_refresh_cookie(results: List[dict]) -> bool:
    for result in results:
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
    )

    browser_info = hub.start_browser(
        CONTAINER_CODE,
        enable_cdp=True,
        open_url="https://app.ahrefs.com",
    )
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


def fetch_fresh_results(domains: List[str], country: str, force_refresh: bool = False) -> List[dict]:
    client = get_ahrefs_client(force_refresh=force_refresh)
    results = client.batch_get_domain_rating(domains, country=country)

    if should_refresh_cookie(results) and not force_refresh:
        invalidate_cookie_cache()
        client = get_ahrefs_client(force_refresh=True)
        results = client.batch_get_domain_rating(domains, country=country)

    return results


def query_domains_with_cache(domains: List[str], country: str) -> dict:
    normalized_country = normalize_country(country)
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
        cached_result = result_cache.get(domain, normalized_country)
        if cached_result:
            ordered_results[index] = cached_result
            cached_domains += 1
            continue

        missing_domains.append(domain)
        missing_indexes.append(index)

    if missing_domains:
        fresh_results = fetch_fresh_results(missing_domains, normalized_country)
        for index, requested_domain, result in zip(missing_indexes, missing_domains, fresh_results):
            normalized_result_domain = normalize_domain(result.get("domain", requested_domain))
            result["domain"] = normalized_result_domain
            ordered_results[index] = result
            if should_cache_result(result):
                result_cache.set(normalized_result_domain, normalized_country, result)

    live_domains = len(missing_domains)
    return {
        "results": [result for result in ordered_results if result is not None],
        "cached_domains": cached_domains,
        "live_domains": live_domains,
        "source": detect_result_source(cached_domains, live_domains),
    }


def process_query_task(task_id: str, domains: List[str], country: str) -> None:
    try:
        tasks_storage[task_id]["status"] = "processing"
        query_output = query_domains_with_cache(domains, country)
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
        "version": "2.2.0",
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
    }


@app.post("/api/query", response_model=TaskResponse, tags=["Query"])
async def query_domain(request: QueryRequest, background_tasks: BackgroundTasks):
    domain = normalize_domain(request.domain)
    country = normalize_country(request.country)
    task_id = str(uuid.uuid4())

    tasks_storage[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "domains": [domain],
        "country": country,
        "source": None,
        "cached_domains": 0,
        "live_domains": 1,
    }

    cached_result = result_cache.get(domain, country)
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

    background_tasks.add_task(
        process_query_task,
        task_id,
        [domain],
        country,
    )

    return TaskResponse(
        task_id=task_id,
        status="pending",
        message="Task created and processing",
        source="live",
        cached_domains=0,
        live_domains=1,
    )


@app.post("/api/batch", response_model=TaskResponse, tags=["Query"])
async def batch_query(request: BatchQueryRequest, background_tasks: BackgroundTasks):
    domains = []
    for domain in request.domains:
        normalized_domain = normalize_domain(domain)
        if normalized_domain:
            domains.append(normalized_domain)
    country = normalize_country(request.country)
    task_id = str(uuid.uuid4())

    tasks_storage[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "domains": domains,
        "country": country,
        "source": None,
        "cached_domains": 0,
        "live_domains": len(domains),
    }

    cached_results: List[Optional[dict]] = []
    all_cached = True
    for domain in domains:
        cached_result = result_cache.get(domain, country)
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

    background_tasks.add_task(
        process_query_task,
        task_id,
        domains,
        country,
    )

    return TaskResponse(
        task_id=task_id,
        status="pending",
        message=f"Task created and processing {len(domains)} domains",
        source=detect_result_source(cached_domains, live_domains),
        cached_domains=cached_domains,
        live_domains=live_domains,
    )


@app.get("/api/result/{task_id}", response_model=TaskResult, tags=["Query"])
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


@app.get("/api/tasks", tags=["Query"])
async def list_tasks():
    return {
        "total": len(tasks_storage),
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
