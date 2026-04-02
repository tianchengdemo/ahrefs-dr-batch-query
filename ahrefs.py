# -*- coding: utf-8 -*-
"""
Ahrefs API 客户端 — 通过 SOCKS5 代理查询 Domain Rating (DR)
"""

import json
import time
import urllib.parse
import requests

from config import (
    AHREFS_BASE_URL,
    DEFAULT_HEADERS,
    DEFAULT_COUNTRY,
    REQUEST_DELAY,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
)


class AhrefsClient:
    """通过已登录的 Cookie 和 SOCKS5 代理查询 Ahrefs 数据"""

    def __init__(self, cookie_header, proxy_url=None):
        """
        Args:
            cookie_header: Cookie 字符串 ("name1=val1; name2=val2; ...")
            proxy_url: SOCKS5 代理 URL ("socks5://host:port") 或 None
        """
        self.cookie_header = cookie_header
        self.proxy_url = proxy_url
        self.base_url = AHREFS_BASE_URL.rstrip("/")

        # 构建 session
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.session.headers["cookie"] = self.cookie_header

        if self.proxy_url:
            self.session.proxies = {
                "http": self.proxy_url,
                "https": self.proxy_url,
            }
            print(f"[Ahrefs] 使用代理: {self.proxy_url}")

    def _build_dr_input(self, domain, country=None):
        """
        构建 seGetDomainRating 请求的 input 参数

        Args:
            domain: 目标域名（如 "example.com"）
            country: 国家代码（如 "us", "br"）
        """
        country = country or DEFAULT_COUNTRY

        # 确保域名后面有 /
        target = domain.rstrip("/") + "/"

        input_obj = {
            "args": {
                "mode": "subdomains",
                "protocol": "https",
                "url": target,
                "multiTarget": [
                    "Single",
                    {
                        "target": target,
                        "mode": "subdomains",
                        "protocol": "https",
                    },
                ],
                "compareDate": ["Ago", ["Month"]],
                "country": country,
                "backlinksFilter": None,
                "best_links_filter": "showAll",
                "competitors": [],
            }
        }
        return json.dumps(input_obj, separators=(",", ":"))

    def _build_timeout_result(self, domain, error):
        return {
            "domain": domain,
            "domain_rating": None,
            "ahrefs_rank": None,
            "dr_delta": None,
            "ar_delta": None,
            "error": error,
            "raw_response": None,
        }

    def get_domain_rating(self, domain, country=None, deadline_ts=None):
        """
        查询单个域名的 Domain Rating

        Args:
            domain: 目标域名
            country: 国家代码

        Returns:
            dict — {
                "domain": str,
                "domain_rating": float,
                "ahrefs_rank": int,
                "raw_response": dict  (完整响应)
            }
        """
        input_str = self._build_dr_input(domain, country)
        url = f"{self.base_url}/v4/seGetDomainRating"
        params = {"input": input_str}

        # 设置 referer
        referer_target = urllib.parse.quote(f"https://{domain}", safe="")
        self.session.headers["referer"] = (
            f"{self.base_url}/v2-site-explorer/overview?"
            f"target={referer_target}&mode=subdomains&country={country or DEFAULT_COUNTRY}"
        )

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                request_timeout = REQUEST_TIMEOUT
                if deadline_ts is not None:
                    remaining = deadline_ts - time.monotonic()
                    if remaining <= 0:
                        return self._build_timeout_result(domain, "Task deadline exceeded")
                    request_timeout = min(REQUEST_TIMEOUT, max(1.0, remaining))

                print(f"[Ahrefs] 查询 DR: {domain} (尝试 {attempt}/{MAX_RETRIES})")
                resp = self.session.get(url, params=params, timeout=request_timeout)

                if resp.status_code == 403:
                    print(f"[Ahrefs] ⚠ 403 Forbidden — Cookie 可能已过期或被封")
                    return {
                        "domain": domain,
                        "domain_rating": None,
                        "ahrefs_rank": None,
                        "error": "403 Forbidden - Cookie过期或IP被封",
                        "raw_response": None,
                    }

                if resp.status_code == 429:
                    wait = min(30, REQUEST_DELAY * attempt * 3)
                    print(f"[Ahrefs] ⚠ 429 限流，等待 {wait}s 后重试...")
                    if deadline_ts is not None:
                        remaining = deadline_ts - time.monotonic()
                        if remaining <= 0:
                            return self._build_timeout_result(domain, "Task deadline exceeded")
                        wait = min(wait, remaining)
                    time.sleep(wait)
                    continue

                resp.raise_for_status()
                data = resp.json()

                # 解析响应
                result = {
                    "domain": domain,
                    "domain_rating": None,
                    "ahrefs_rank": None,
                    "raw_response": data,
                }

                # 响应格式: ['Ok', {'ahrefsRank': {...}, 'domainRating': {...}}]
                # 或旧格式: {"result": {"data": {...}}}
                inner = data

                # 如果是数组格式，取第二个元素
                if isinstance(data, list) and len(data) >= 2:
                    inner = data[1]
                elif "result" in data:
                    inner = data["result"]
                    if "data" in inner:
                        inner = inner["data"]
                elif "data" in data:
                    inner = data["data"]

                if not isinstance(inner, dict):
                    inner = {}

                if "domainRating" in inner and isinstance(inner["domainRating"], dict):
                    dr_info = inner["domainRating"]
                    result["domain_rating"] = dr_info.get("value")
                    result["dr_delta"] = dr_info.get("delta")

                if "ahrefsRank" in inner and isinstance(inner["ahrefsRank"], dict):
                    ar_info = inner["ahrefsRank"]
                    result["ahrefs_rank"] = ar_info.get("value")
                    result["ar_delta"] = ar_info.get("delta")

                status = "[OK]" if result["domain_rating"] is not None else "[FAIL]"
                print(
                    f"[Ahrefs] {status} {domain} → DR: {result['domain_rating']}, "
                    f"AR: {result['ahrefs_rank']}"
                )
                return result

            except requests.exceptions.ProxyError as e:
                print(f"[Ahrefs] [ERROR] 代理连接失败: {e}")
                if attempt == MAX_RETRIES:
                    return {
                        "domain": domain,
                        "domain_rating": None,
                        "ahrefs_rank": None,
                        "error": f"代理连接失败: {e}",
                        "raw_response": None,
                    }
                sleep_for = REQUEST_DELAY
                if deadline_ts is not None:
                    remaining = deadline_ts - time.monotonic()
                    if remaining <= 0:
                        return self._build_timeout_result(domain, "Task deadline exceeded")
                    sleep_for = min(sleep_for, remaining)
                time.sleep(sleep_for)

            except requests.exceptions.RequestException as e:
                print(f"[Ahrefs] [ERROR] 请求失败: {e}")
                if attempt == MAX_RETRIES:
                    return {
                        "domain": domain,
                        "domain_rating": None,
                        "ahrefs_rank": None,
                        "error": str(e),
                        "raw_response": None,
                    }
                sleep_for = REQUEST_DELAY
                if deadline_ts is not None:
                    remaining = deadline_ts - time.monotonic()
                    if remaining <= 0:
                        return self._build_timeout_result(domain, "Task deadline exceeded")
                    sleep_for = min(sleep_for, remaining)
                time.sleep(sleep_for)

            except (json.JSONDecodeError, KeyError) as e:
                print(f"[Ahrefs] [ERROR] 解析响应失败: {e}")
                return {
                    "domain": domain,
                    "domain_rating": None,
                    "ahrefs_rank": None,
                    "error": f"解析失败: {e}",
                    "raw_response": resp.text if 'resp' in dir() else None,
                }

    def batch_get_domain_rating(self, domains, country=None, delay=None, deadline_ts=None):
        """
        批量查询多个域名的 DR

        Args:
            domains: 域名列表
            country: 国家代码
            delay: 请求间隔秒数（默认使用配置的 REQUEST_DELAY）

        Returns:
            list[dict] — 每个元素为 get_domain_rating 的返回值
        """
        delay = delay if delay is not None else REQUEST_DELAY
        results = []
        total = len(domains)

        print(f"\n{'='*60}")
        print(f"  开始批量查询 {total} 个域名的 Domain Rating")
        print(f"{'='*60}\n")

        for index, raw_domain in enumerate(domains):
            domain = raw_domain.strip()
            if not domain:
                continue

            if deadline_ts is not None and time.monotonic() >= deadline_ts:
                for remaining_domain in domains[index:]:
                    remaining_domain = remaining_domain.strip()
                    if remaining_domain:
                        results.append(
                            self._build_timeout_result(
                                remaining_domain,
                                "Task deadline exceeded",
                            )
                        )
                break

            display_index = index + 1
            print(f"\n--- [{display_index}/{total}] {domain} ---")
            result = self.get_domain_rating(domain, country, deadline_ts=deadline_ts)
            results.append(result)

            # 除最后一个外，等待指定间隔
            if display_index < total:
                print(f"[Ahrefs] 等待 {delay}s ...")
                sleep_for = delay
                if deadline_ts is not None:
                    remaining = deadline_ts - time.monotonic()
                    if remaining <= 0:
                        continue
                    sleep_for = min(delay, remaining)
                time.sleep(sleep_for)

        return results

    def get_overview_data(self, domain, country=None):
        """
        获取 Ahrefs Site Explorer 概览页面的完整数据
        包含多个 API 端点的数据

        Args:
            domain: 目标域名
            country: 国家代码

        Returns:
            dict — 包含 DR, UR, 反链, 自然搜索流量等全部概览数据
        """
        country = country or DEFAULT_COUNTRY
        target = domain.rstrip("/") + "/"

        # 所有需要查询的概览 API 端点
        endpoints = {
            "domainRating": "/v4/seGetDomainRating",
            "urlRating": "/v4/seGetUrlRating",
            "backlinksStats": "/v4/seOverviewBacklinksStatsAll",
            "pagesByTraffic": "/v4/seGetPagesByTrafficTopInput",
        }

        base_args = {
            "mode": "subdomains",
            "protocol": "https",
            "url": target,
            "multiTarget": [
                "Single",
                {"target": target, "mode": "subdomains", "protocol": "https"},
            ],
            "compareDate": ["Ago", ["Month"]],
            "country": country,
            "backlinksFilter": None,
            "best_links_filter": "showAll",
            "competitors": [],
        }

        overview = {"domain": domain, "country": country}

        for name, path in endpoints.items():
            input_str = json.dumps({"args": base_args}, separators=(",", ":"))
            url = f"{self.base_url}{path}"

            try:
                resp = self.session.get(
                    url, params={"input": input_str}, timeout=REQUEST_TIMEOUT
                )
                if resp.status_code == 200:
                    overview[name] = resp.json()
                    print(f"[Ahrefs] [OK] {name}")
                else:
                    overview[name] = {"error": f"HTTP {resp.status_code}"}
                    print(f"[Ahrefs] [ERROR] {name}: HTTP {resp.status_code}")
            except Exception as e:
                overview[name] = {"error": str(e)}
                print(f"[Ahrefs] [ERROR] {name}: {e}")

            time.sleep(1)  # 小间隔避免限流

        return overview
