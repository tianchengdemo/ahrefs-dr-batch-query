# -*- coding: utf-8 -*-
"""
API 客户端 - 用于 Bot 调用 API 服务
"""

import requests
import time
from typing import List, Dict, Optional
from .config import API_BASE_URL, POLL_INTERVAL, QUERY_TIMEOUT


class APIClient:
    """API 客户端"""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip("/")

    def health_check(self) -> bool:
        """健康检查"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def query_domain(self, domain: str, country: str = "us") -> Optional[Dict]:
        """
        查询单个域名

        Args:
            domain: 域名
            country: 国家代码

        Returns:
            查询结果字典，失败返回 None
        """
        try:
            # 创建查询任务
            response = requests.post(
                f"{self.base_url}/api/query",
                json={"domain": domain, "country": country},
                timeout=10
            )

            if response.status_code != 200:
                return None

            task_data = response.json()
            task_id = task_data.get("task_id")

            if not task_id:
                return None

            # 轮询获取结果
            start_time = time.time()
            while time.time() - start_time < QUERY_TIMEOUT:
                result = self.get_task_result(task_id)

                if not result:
                    return None

                status = result.get("status")

                if status == "completed":
                    results = result.get("results", [])
                    return results[0] if results else None
                elif status == "failed":
                    return {"error": result.get("error", "查询失败")}

                time.sleep(POLL_INTERVAL)

            return {"error": "查询超时"}

        except Exception as e:
            return {"error": str(e)}

    def batch_query(self, domains: List[str], country: str = "us") -> Optional[List[Dict]]:
        """
        批量查询域名

        Args:
            domains: 域名列表
            country: 国家代码

        Returns:
            查询结果列表，失败返回 None
        """
        try:
            # 创建批量查询任务
            response = requests.post(
                f"{self.base_url}/api/batch",
                json={"domains": domains, "country": country},
                timeout=10
            )

            if response.status_code != 200:
                return None

            task_data = response.json()
            task_id = task_data.get("task_id")

            if not task_id:
                return None

            # 轮询获取结果
            start_time = time.time()
            while time.time() - start_time < QUERY_TIMEOUT * len(domains):
                result = self.get_task_result(task_id)

                if not result:
                    return None

                status = result.get("status")

                if status == "completed":
                    return result.get("results", [])
                elif status == "failed":
                    return [{"error": result.get("error", "查询失败")}]

                time.sleep(POLL_INTERVAL)

            return [{"error": "查询超时"}]

        except Exception as e:
            return [{"error": str(e)}]

    def get_task_result(self, task_id: str) -> Optional[Dict]:
        """
        获取任务结果

        Args:
            task_id: 任务 ID

        Returns:
            任务结果字典，失败返回 None
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/result/{task_id}",
                timeout=5
            )

            if response.status_code == 200:
                return response.json()

            return None

        except Exception:
            return None

    def list_tasks(self) -> Optional[Dict]:
        """
        列出所有任务

        Returns:
            任务列表字典，失败返回 None
        """
        try:
            response = requests.get(f"{self.base_url}/api/tasks", timeout=5)

            if response.status_code == 200:
                return response.json()

            return None

        except Exception:
            return None
