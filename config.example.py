# -*- coding: utf-8 -*-
"""
Example configuration for the Ahrefs query service.
Copy this file to config.py and fill in your real values.
"""

# ============================================================
# HubStudio settings
# ============================================================

HUBSTUDIO_API_BASE = "http://127.0.0.1:6873"
# When running in Docker, this is usually "host.docker.internal".
HUBSTUDIO_CDP_HOST = "127.0.0.1"
APP_ID = "your-app-id"
APP_SECRET = "your-app-secret"
CONTAINER_CODE = "your-container-code"


# ============================================================
# Ahrefs cookie fallback
# ============================================================

def _load_cookie():
    try:
        with open("cookies.txt", "r", encoding="utf-8") as file:
            return file.read().strip()
    except FileNotFoundError:
        return ""


AHREFS_COOKIE = _load_cookie()


# ============================================================
# Proxy settings
# ============================================================

# Leave empty to use the proxy configured in HubStudio.
SOCKS5_PROXY = ""


# ============================================================
# Ahrefs request settings
# ============================================================

AHREFS_BASE_URL = "https://app.ahrefs.com"

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
# Query settings
# ============================================================

DEFAULT_COUNTRY = "us"
REQUEST_DELAY = 2
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3


# ============================================================
# Cache settings
# ============================================================

# Reuse the HubStudio cookie in memory to avoid restarting the browser
# on every query. Set to 0 to disable cookie caching.
COOKIE_CACHE_TTL_MINUTES = 30

# Persist successful domain query results in SQLite.
RESULT_CACHE_ENABLED = True

# Cache database file path. Relative paths are resolved from the project root.
RESULT_CACHE_DB_PATH = ".omc/result_cache.sqlite3"

# Keep successful query results for this many days.
# Set to 0 to disable result caching.
RESULT_CACHE_TTL_DAYS = 30


# ============================================================
# API auth settings
# ============================================================

# Require X-API-Key on protected API endpoints.
API_AUTH_ENABLED = True

# Multiple keys are supported.
API_KEYS = [
    "replace-with-a-long-random-key",
    "optional-second-key",
]
