# -*- coding: utf-8 -*-
"""
HubStudio API client.
"""

import json

import requests


class HubStudioClient:
    def __init__(
        self,
        api_base: str = "http://127.0.0.1:6873",
        app_id: str = "",
        app_secret: str = "",
        cdp_host: str = "127.0.0.1",
    ):
        self.api_base = api_base.rstrip("/")
        self.app_id = app_id
        self.app_secret = app_secret
        self.cdp_host = cdp_host
        self.session = requests.Session()

    def _request(self, endpoint, method="POST", **kwargs):
        url = f"{self.api_base}{endpoint}"
        headers = kwargs.pop("headers", {})
        headers.update(
            {
                "app-id": self.app_id,
                "app-secret": self.app_secret,
                "Content-Type": "application/json",
            }
        )

        response = self.session.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        result = response.json()

        if result.get("code") != 0:
            raise Exception(f"HubStudio API Error: {result.get('msg', 'Unknown error')}")

        return result.get("data", {})

    def stop_browser(self, container_code):
        return self._request(
            "/api/v1/browser/stop",
            json={"containerCode": int(container_code)},
        )

    def start_browser(self, container_code, enable_cdp=True, open_url=None):
        params = {"containerCode": int(container_code)}

        if enable_cdp:
            params["args"] = ["--remote-allow-origins=*"]

        if open_url:
            params["containerTabs"] = [open_url]

        return self._request(
            "/api/v1/browser/start",
            json=params,
        )

    def get_cookies_via_cdp(self, debugging_port, domain="ahrefs.com"):
        try:
            pages = requests.get(
                f"http://{self.cdp_host}:{debugging_port}/json",
                timeout=5,
            ).json()
            if not pages:
                return []

            import websocket

            ws_url = pages[0]["webSocketDebuggerUrl"]
            websocket_connection = websocket.create_connection(ws_url, timeout=10)
            command = {
                "id": 1,
                "method": "Network.getCookies",
                "params": {},
            }
            websocket_connection.send(json.dumps(command))
            response = json.loads(websocket_connection.recv())
            websocket_connection.close()

            all_cookies = response.get("result", {}).get("cookies", [])
            filtered = []
            domain_lower = domain.lower()
            for cookie in all_cookies:
                cookie_domain = cookie.get("domain", "").lower()
                if domain_lower in cookie_domain or cookie_domain.endswith(domain_lower):
                    filtered.append(
                        {
                            "name": cookie.get("name"),
                            "value": cookie.get("value"),
                            "httpOnly": cookie.get("httpOnly", False),
                        }
                    )

            return filtered

        except Exception as exc:
            print(f"[CDP] Failed to get cookies: {exc}")
            return []

    def export_cookies(self, container_code, domain="ahrefs.com"):
        data = self._request(
            "/api/v1/env/export-cookie",
            json={"containerCode": int(container_code)},
        )
        cookies_json = json.loads(data) if isinstance(data, str) else data

        filtered = []
        domain_lower = domain.lower()
        for cookie in cookies_json:
            cookie_domain = cookie.get("Domain", "").lower()
            if domain_lower in cookie_domain or cookie_domain.endswith(domain_lower):
                filtered.append(
                    {
                        "name": cookie.get("Name"),
                        "value": cookie.get("Value"),
                    }
                )
        return filtered

    def get_env_list(self):
        data = self._request("/api/v1/env/list", json={})
        return data.get("list", [])

    def get_proxy_for_env(self, container_code):
        environments = self.get_env_list()
        for environment in environments:
            if str(environment.get("containerCode")) == str(container_code):
                proxy = environment.get("proxyConfig", {})
                if proxy.get("proxyType") == "socks5":
                    return self.build_proxy_url(proxy)
        return None

    def build_cookie_header(self, cookies):
        return "; ".join(
            [
                f"{cookie['name']}={cookie['value']}"
                for cookie in cookies
                if cookie.get("name") and cookie.get("value")
            ]
        )

    def build_proxy_url(self, proxy_config):
        host = proxy_config.get("proxyHost")
        port = proxy_config.get("proxyPort")
        user = proxy_config.get("proxyUser")
        password = proxy_config.get("proxyPassword")

        if not host or not port:
            return None

        if user and password:
            return f"socks5://{user}:{password}@{host}:{port}"
        return f"socks5://{host}:{port}"
