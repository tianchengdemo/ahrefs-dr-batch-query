import json
import sqlite3
import time
from pathlib import Path
from typing import Optional


class DomainResultCache:
    def __init__(
        self,
        db_path: str,
        ttl_days: int,
        enabled: bool = True,
        redis_enabled: bool = False,
        redis_url: str = "",
        redis_ttl_seconds: int = 21600,
        redis_key_prefix: str = "ahrefs:domain-cache:",
    ):
        self.enabled = enabled and ttl_days > 0
        self.ttl_days = ttl_days
        self.db_path = Path(db_path)
        if not self.db_path.is_absolute():
            self.db_path = Path.cwd() / self.db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.redis_enabled = self.enabled and redis_enabled and bool(redis_url)
        self.redis_url = redis_url
        self.redis_ttl_seconds = max(redis_ttl_seconds, 1)
        self.redis_key_prefix = redis_key_prefix
        self.redis_client = None

        self._init_db()
        self._init_redis()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        if not self.enabled:
            return

        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS domain_query_cache (
                    domain TEXT NOT NULL,
                    country TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    fetched_at INTEGER NOT NULL,
                    expires_at INTEGER NOT NULL,
                    PRIMARY KEY (domain, country)
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_domain_query_cache_expires_at
                ON domain_query_cache (expires_at)
                """
            )

    def _init_redis(self) -> None:
        if not self.redis_enabled:
            return

        try:
            import redis

            self.redis_client = redis.Redis.from_url(
                self.redis_url,
                decode_responses=True,
            )
            self.redis_client.ping()
        except Exception as exc:
            print(f"[Cache] Redis disabled: {exc}")
            self.redis_client = None
            self.redis_enabled = False

    def _redis_key(self, domain: str, country: str) -> str:
        return f"{self.redis_key_prefix}{country}:{domain}"

    def _serialize_result(self, domain: str, result: dict, fetched_at: int, expires_at: int) -> dict:
        return {
            "domain": result.get("domain", domain),
            "domain_rating": result.get("domain_rating"),
            "ahrefs_rank": result.get("ahrefs_rank"),
            "dr_delta": result.get("dr_delta"),
            "ar_delta": result.get("ar_delta"),
            "error": result.get("error"),
            "cached_at": fetched_at,
            "cache_expires_at": expires_at,
        }

    def _set_redis(self, domain: str, country: str, payload: dict) -> None:
        if not self.redis_enabled or not self.redis_client:
            return

        try:
            ttl = max(min(payload["cache_expires_at"] - int(time.time()), self.redis_ttl_seconds), 1)
            self.redis_client.set(
                self._redis_key(domain, country),
                json.dumps(payload, ensure_ascii=False),
                ex=ttl,
            )
        except Exception as exc:
            print(f"[Cache] Redis set failed: {exc}")

    def prune_expired(self) -> None:
        if not self.enabled:
            return

        now_ts = int(time.time())
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM domain_query_cache WHERE expires_at <= ?",
                (now_ts,),
            )

    def get(self, domain: str, country: str) -> Optional[dict]:
        if not self.enabled:
            return None

        if self.redis_enabled and self.redis_client:
            try:
                cached_value = self.redis_client.get(self._redis_key(domain, country))
                if cached_value:
                    return json.loads(cached_value)
            except Exception as exc:
                print(f"[Cache] Redis get failed: {exc}")

        now_ts = int(time.time())
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT result_json, fetched_at, expires_at
                FROM domain_query_cache
                WHERE domain = ? AND country = ? AND expires_at > ?
                """,
                (domain, country, now_ts),
            ).fetchone()

        if not row:
            return None

        result = json.loads(row[0])
        payload = self._serialize_result(domain, result, row[1], row[2])
        self._set_redis(domain, country, payload)
        return payload

    def set(self, domain: str, country: str, result: dict) -> None:
        if not self.enabled:
            return

        now_ts = int(time.time())
        expires_at = now_ts + self.ttl_days * 24 * 60 * 60
        stored_result = self._serialize_result(domain, result, now_ts, expires_at)

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO domain_query_cache (
                    domain,
                    country,
                    result_json,
                    fetched_at,
                    expires_at
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(domain, country) DO UPDATE SET
                    result_json = excluded.result_json,
                    fetched_at = excluded.fetched_at,
                    expires_at = excluded.expires_at
                """,
                (
                    domain,
                    country,
                    json.dumps(
                        {
                            "domain": stored_result["domain"],
                            "domain_rating": stored_result["domain_rating"],
                            "ahrefs_rank": stored_result["ahrefs_rank"],
                            "dr_delta": stored_result["dr_delta"],
                            "ar_delta": stored_result["ar_delta"],
                            "error": stored_result["error"],
                        },
                        ensure_ascii=False,
                    ),
                    now_ts,
                    expires_at,
                ),
            )

        self._set_redis(domain, country, stored_result)
