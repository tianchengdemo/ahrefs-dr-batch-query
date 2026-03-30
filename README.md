# Ahrefs Query Service

基于 HubStudio 和 Ahrefs 会话的域名查询服务，提供：

- CLI 查询
- FastAPI 接口
- Telegram Bot
- Cookie 复用缓存
- 域名结果 SQLite 缓存

## 当前行为

- API 不再每次查询都重启浏览器取 Cookie。
- Cookie 默认在内存中复用 `30` 分钟。
- 成功查询的域名结果默认缓存 `30` 天。
- 结果缓存按 `domain + country` 存储。
- Bot 正确启动方式是 `python -m bot.main`，不是 `python bot/main.py`。

## 目录

```text
ahrefs/
├── api/
│   └── main.py
├── bot/
│   ├── api_client.py
│   ├── config.py
│   ├── handlers.py
│   └── main.py
├── ahrefs.py
├── config.example.py
├── hubstudio.py
├── main.py
├── requirements.txt
└── result_cache.py
```

## 依赖

- Python 3.10+
- HubStudio Local API
- 已登录 Ahrefs 的 HubStudio 环境

安装依赖：

```powershell
cd D:\DEV\ahrefs
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 配置

复制 `config.example.py` 为 `config.py`，然后填写：

```python
HUBSTUDIO_API_BASE = "http://127.0.0.1:6873"
APP_ID = "your-app-id"
APP_SECRET = "your-app-secret"
CONTAINER_CODE = "your-container-code"
```

缓存相关配置：

```python
COOKIE_CACHE_TTL_MINUTES = 30
RESULT_CACHE_ENABLED = True
RESULT_CACHE_DB_PATH = ".omc/result_cache.sqlite3"
RESULT_CACHE_TTL_DAYS = 30
```

说明：

- `COOKIE_CACHE_TTL_MINUTES`
  控制 Cookie 在内存中复用多久。
- `RESULT_CACHE_TTL_DAYS`
  控制域名查询结果保留多久。
- `RESULT_CACHE_DB_PATH`
  是 SQLite 缓存库路径。

## 启动 API

```powershell
cd D:\DEV\ahrefs
.\.venv\Scripts\python.exe -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

健康检查：

```powershell
curl http://127.0.0.1:8000/health
```

`/health` 会返回当前缓存开关和 TTL。

## 启动 Bot

先启动 API，再启动 Bot：

```powershell
cd D:\DEV\ahrefs
.\.venv\Scripts\python.exe -m bot.main
```

## 缓存说明

### Cookie 缓存

- API 首次需要实时查询时，会从 HubStudio 获取 Cookie。
- 之后在 TTL 内复用内存中的 Cookie。
- 如果 Ahrefs 返回 `403`，会自动失效并重新刷新 Cookie。

### 结果缓存

- 单域名和批量查询都会先查 SQLite。
- 批量查询只会实时请求未命中的域名。
- 例如第一次只查过 `example.com`，之后执行：

```text
/batch example.com google.com github.com
```

则只会实时请求 `google.com` 和 `github.com`。

## CLI

单域名：

```powershell
.\.venv\Scripts\python.exe main.py --domains "example.com"
```

多域名：

```powershell
.\.venv\Scripts\python.exe main.py --domains "example.com,google.com,github.com"
```

## 相关文档

- [API.md](API.md)
- [BOT.md](BOT.md)
- [FILES.md](FILES.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
