# -*- coding: utf-8 -*-
"""
Ahrefs DR 批量查询工具 - 配置文件示例
复制此文件为 config.py 并填写你的配置
"""

# ============================================================
# HubStudio 指纹浏览器配置
# ============================================================

# HubStudio Local API 地址
# 从 HubStudio 客户端 → 设置 → Local API 获取
HUBSTUDIO_API_BASE = "http://127.0.0.1:6873"

# APP ID - 从 HubStudio → 设置 → Local API 获取
APP_ID = "你的APP_ID"

# APP Secret - 从 HubStudio → 设置 → Local API 获取
APP_SECRET = "你的APP_SECRET"

# 环境 ID - 已登录 Ahrefs 的 HubStudio 环境 ID
# 在 HubStudio 环境列表中查看 containerCode
CONTAINER_CODE = "你的环境ID"

# ============================================================
# Ahrefs Cookie 配置（可选）
# 优先使用 CDP 自动获取，此配置仅作为回退方案
# ============================================================

def _load_cookie():
    """从 cookies.txt 加载手动配置的 Cookie（回退方案）"""
    try:
        with open("cookies.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

AHREFS_COOKIE = _load_cookie()

# ============================================================
# SOCKS5 代理配置（可选）
# 优先从 HubStudio 环境自动获取，此配置用于手动覆盖
# ============================================================

# 留空则自动从 HubStudio 环境获取代理配置
# 格式: "socks5://user:pass@host:port" 或 "socks5://host:port"
SOCKS5_PROXY = ""

# ============================================================
# Ahrefs API 配置
# ============================================================

# Ahrefs 网站基地址
AHREFS_BASE_URL = "https://app.ahrefs.com"

# 默认请求头（模拟浏览器）
DEFAULT_HEADERS = {
    "accept": "*/*",
    "accept-language": "vi-VN,vi;q=0.9",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
    "sec-ch-ua-arch": '"x86"',
    "sec-ch-ua-bitness": '"64"',
    "sec-ch-ua-full-version": '"127.0.6533.51"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-model": '""',
    "sec-ch-ua-platform": '"Windows"',
    "sec-ch-ua-platform-version": '"10.0.0"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
}

# ============================================================
# 查询配置
# ============================================================

# 默认国家代码
DEFAULT_COUNTRY = "us"

# 批量查询时每个请求之间的延迟（秒）
REQUEST_DELAY = 2

# 请求超时（秒）
REQUEST_TIMEOUT = 30

# 失败重试次数
MAX_RETRIES = 3

# ============================================================
# 配置说明
# ============================================================

"""
必填配置：
1. HUBSTUDIO_API_BASE - HubStudio API 地址
2. APP_ID - HubStudio APP ID
3. APP_SECRET - HubStudio APP Secret
4. CONTAINER_CODE - 已登录 Ahrefs 的环境 ID

可选配置：
1. SOCKS5_PROXY - 手动指定代理（留空则自动获取）
2. AHREFS_COOKIE - 手动配置 Cookie（留空则自动获取）
3. DEFAULT_COUNTRY - 默认查询国家
4. REQUEST_DELAY - 请求间隔
5. REQUEST_TIMEOUT - 请求超时
6. MAX_RETRIES - 重试次数

获取 HubStudio 配置的步骤：
1. 打开 HubStudio 客户端
2. 点击右上角 设置 图标
3. 选择 Local API
4. 复制 API 接口地址、APP ID、APP Secret
5. 在环境列表中找到已登录 Ahrefs 的环境
6. 复制该环境的 containerCode

注意事项：
- 确保 HubStudio 客户端正在运行
- 确保 Local API 状态为"正常"
- 确保环境已登录 Ahrefs 账号
- 确保环境配置了可用的 SOCKS5 代理
- 程序会自动通过 CDP 获取所有 Cookie（包括 HttpOnly）
- 无需手动配置 BSSESSID 等会话 Cookie
"""
