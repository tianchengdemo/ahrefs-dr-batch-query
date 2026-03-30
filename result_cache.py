import json
import sqlite3
import time
from pathlib import Path
from typing import Optional


class DomainResultCache:
    def __init__(self, db_path: str, ttl_days: int, enabled: bool = True):
        self.enabled = enabled and ttl_days > 0
        self.ttl_days = ttl_days
        self.db_path = Path(db_path)
        if not self.db_path.is_absolute():
            self.db_path = Path.cwd() / self.db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

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
        result["cached_at"] = row[1]
        result["cache_expires_at"] = row[2]
        return result

    def set(self, domain: str, country: str, result: dict) -> None:
        if not self.enabled:
            return

        now_ts = int(time.time())
        expires_at = now_ts + self.ttl_days * 24 * 60 * 60
        stored_result = {
            "domain": result.get("domain", domain),
            "domain_rating": result.get("domain_rating"),
            "ahrefs_rank": result.get("ahrefs_rank"),
            "dr_delta": result.get("dr_delta"),
            "ar_delta": result.get("ar_delta"),
            "error": result.get("error"),
        }

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
                    json.dumps(stored_result, ensure_ascii=False),
                    now_ts,
                    expires_at,
                ),
            )
