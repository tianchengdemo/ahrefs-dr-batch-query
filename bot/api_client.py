# -*- coding: utf-8 -*-
"""
API client used by the Telegram Bot.
"""

import time
from typing import Dict, List, Optional

import requests

from .config import API_BASE_URL, POLL_INTERVAL, QUERY_TIMEOUT


class APIClient:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip("/")

    @staticmethod
    def _attach_source(result: Dict, source: Optional[str]) -> Dict:
        enriched = dict(result)
        if source:
            enriched["_source"] = source
        return enriched

    def health_check(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def query_domain(self, domain: str, country: str = "us") -> Optional[Dict]:
        try:
            response = requests.post(
                f"{self.base_url}/api/query",
                json={"domain": domain, "country": country},
                timeout=10,
            )

            if response.status_code != 200:
                return None

            task_data = response.json()
            task_id = task_data.get("task_id")
            status = task_data.get("status")
            results = task_data.get("results", [])
            source = task_data.get("source")

            if not task_id:
                return None

            if status == "completed":
                return self._attach_source(results[0], source) if results else None
            if status == "failed":
                return {"error": task_data.get("error", "Query failed")}

            start_time = time.time()
            while time.time() - start_time < QUERY_TIMEOUT:
                result = self.get_task_result(task_id)

                if not result:
                    return None

                status = result.get("status")

                if status == "completed":
                    results = result.get("results", [])
                    source = result.get("source")
                    return self._attach_source(results[0], source) if results else None
                if status == "failed":
                    return {"error": result.get("error", "Query failed")}

                time.sleep(POLL_INTERVAL)

            return {"error": "Query timeout"}

        except Exception as exc:
            return {"error": str(exc)}

    def batch_query(self, domains: List[str], country: str = "us") -> Optional[List[Dict]]:
        try:
            response = requests.post(
                f"{self.base_url}/api/batch",
                json={"domains": domains, "country": country},
                timeout=10,
            )

            if response.status_code != 200:
                return None

            task_data = response.json()
            task_id = task_data.get("task_id")
            status = task_data.get("status")
            results = task_data.get("results", [])
            source = task_data.get("source")

            if not task_id:
                return None

            if status == "completed":
                return [self._attach_source(result, source) for result in results]
            if status == "failed":
                return [{"error": task_data.get("error", "Batch query failed")}]

            start_time = time.time()
            while time.time() - start_time < QUERY_TIMEOUT * max(len(domains), 1):
                result = self.get_task_result(task_id)

                if not result:
                    return None

                status = result.get("status")

                if status == "completed":
                    source = result.get("source")
                    return [
                        self._attach_source(item, source)
                        for item in result.get("results", [])
                    ]
                if status == "failed":
                    return [{"error": result.get("error", "Batch query failed")}]

                time.sleep(POLL_INTERVAL)

            return [{"error": "Query timeout"}]

        except Exception as exc:
            return [{"error": str(exc)}]

    def get_task_result(self, task_id: str) -> Optional[Dict]:
        try:
            response = requests.get(
                f"{self.base_url}/api/result/{task_id}",
                timeout=5,
            )

            if response.status_code == 200:
                return response.json()

            return None

        except Exception:
            return None

    def list_tasks(self) -> Optional[Dict]:
        try:
            response = requests.get(f"{self.base_url}/api/tasks", timeout=5)

            if response.status_code == 200:
                return response.json()

            return None

        except Exception:
            return None
