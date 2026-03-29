# -*- coding: utf-8 -*-
"""
HubStudio 指纹浏览器 API 客户端
基于官方 API 文档: https://api-docs.hubstudio.cn/
"""

import requests


class HubStudioClient:
    def __init__(self, api_base="http://127.0.0.1:6873", app_id="", app_secret=""):
        self.api_base = api_base
        self.app_id = app_id
        self.app_secret = app_secret
        self.session = requests.Session()

    def _request(self, endpoint, method="POST", **kwargs):
        """发送 API 请求"""
        url = f"{self.api_base}{endpoint}"
        headers = kwargs.pop("headers", {})
        headers.update({
            "app-id": self.app_id,
            "app-secret": self.app_secret,
            "Content-Type": "application/json"
        })

        resp = self.session.request(method, url, headers=headers, **kwargs)
        resp.raise_for_status()
        result = resp.json()

        # HubStudio API 返回格式: {"code": 0, "msg": "Success", "data": {...}}
        if result.get("code") != 0:
            raise Exception(f"HubStudio API Error: {result.get('msg', 'Unknown error')}")

        return result.get("data", {})

    def stop_browser(self, container_code):
        """关闭浏览器环境"""
        data = self._request(
            "/api/v1/browser/stop",
            json={"containerCode": int(container_code)}
        )
        return data

    def start_browser(self, container_code, enable_cdp=True, open_url=None):
        """启动浏览器环境并返回调试端口"""
        params = {"containerCode": int(container_code)}

        # 添加启动参数以允许 CDP 连接
        if enable_cdp:
            params["args"] = ["--remote-allow-origins=*"]

        # 启动时打开指定 URL
        if open_url:
            params["containerTabs"] = [open_url]

        data = self._request(
            "/api/v1/browser/start",
            json=params
        )
        return data

    def get_cookies_via_cdp(self, debugging_port, domain="ahrefs.com"):
        """通过 CDP 协议获取浏览器 Cookie（包括 HttpOnly）"""
        import json

        try:
            # 获取所有页面
            pages = requests.get(f"http://127.0.0.1:{debugging_port}/json", timeout=5).json()
            if not pages:
                return []

            # 使用 websocket 连接到第一个页面
            import websocket
            ws_url = pages[0]["webSocketDebuggerUrl"]
            ws = websocket.create_connection(ws_url, timeout=10)

            # 发送获取 Cookie 命令
            command = {
                "id": 1,
                "method": "Network.getCookies",
                "params": {}
            }
            ws.send(json.dumps(command))
            response = json.loads(ws.recv())
            ws.close()

            # 过滤指定域名的 Cookie
            all_cookies = response.get("result", {}).get("cookies", [])
            filtered = []
            for c in all_cookies:
                cookie_domain = c.get("domain", "").lower()
                if domain.lower() in cookie_domain or cookie_domain.endswith(domain.lower()):
                    filtered.append({
                        "name": c.get("name"),
                        "value": c.get("value"),
                        "httpOnly": c.get("httpOnly", False)
                    })

            return filtered

        except Exception as e:
            print(f"[CDP] 获取 Cookie 失败: {e}")
            return []

    def export_cookies(self, container_code, domain="ahrefs.com"):
        """导出指定环境的 Cookie（不包括 HttpOnly）"""
        import json
        data = self._request(
            "/api/v1/env/export-cookie",
            json={"containerCode": int(container_code)}
        )
        # data 是 JSON 字符串，需要解析
        cookies_json = json.loads(data) if isinstance(data, str) else data

        # 过滤出指定域名的 Cookie
        filtered = []
        for c in cookies_json:
            cookie_domain = c.get("Domain", "").lower()
            domain_lower = domain.lower()
            if domain_lower in cookie_domain or cookie_domain.endswith(domain_lower):
                filtered.append({
                    "name": c.get("Name"),
                    "value": c.get("Value")
                })
        return filtered

    def get_env_list(self):
        """获取环境列表"""
        data = self._request("/api/v1/env/list", json={})
        return data.get("list", [])

    def get_proxy_for_env(self, container_code):
        """获取环境的代理配置"""
        envs = self.get_env_list()
        for env in envs:
            if str(env.get("containerCode")) == str(container_code):
                proxy = env.get("proxyConfig", {})
                if proxy.get("proxyType") == "socks5":
                    return self.build_proxy_url(proxy)
        return None

    def build_cookie_header(self, cookies):
        """构建 Cookie 请求头"""
        return "; ".join([f"{c['name']}={c['value']}" for c in cookies if c.get('name') and c.get('value')])

    def build_proxy_url(self, proxy_config):
        """构建代理 URL"""
        host = proxy_config.get("proxyHost")
        port = proxy_config.get("proxyPort")
        user = proxy_config.get("proxyUser")
        pwd = proxy_config.get("proxyPassword")

        if not host or not port:
            return None

        if user and pwd:
            return f"socks5://{user}:{pwd}@{host}:{port}"
        return f"socks5://{host}:{port}"
