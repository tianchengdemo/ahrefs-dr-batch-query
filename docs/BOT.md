# Telegram Bot

## 定位

Bot 只是客户端：

- 不负责缓存
- 不负责鉴权逻辑
- 不直接查询 Ahrefs
- 所有业务都交给 API

当前行为：

- 单域名查询在默认情况下通常会直接收到 `completed + results`，Bot 不再轮询
- 如果 API 返回 `pending`，例如批量查询或单域名传了 `async_mode = true`，Bot 会轮询 `/api/result/{task_id}`
- Bot 请求头会自动带上 `X-API-Key`

## 启动顺序

先启动 API：

```powershell
cd D:\DEV\ahrefs
.\.venv\Scripts\python.exe -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

再启动 Bot：

```powershell
cd D:\DEV\ahrefs
.\.venv\Scripts\python.exe -m bot.main
```

## Bot 配置

编辑 `bot/config.py`：

```python
TELEGRAM_BOT_TOKEN = "your-bot-token"
API_BASE_URL = "http://localhost:8000"
API_KEY = "your-api-key"
DEFAULT_COUNTRY = "us"
POLL_INTERVAL = 2
QUERY_TIMEOUT = 60
MAX_BATCH_DOMAINS = 20
```

如果 Bot 走线上 API，可改成：

```python
API_BASE_URL = "https://dr.lookav.net"
API_KEY = "your-api-key"
```

说明：

- `API_KEY` 必须和 API 端 `API_KEYS` 中的某一个一致
- `POLL_INTERVAL` 是收到 `pending` 后轮询任务结果的间隔秒数
- `QUERY_TIMEOUT` 是单次查询最长等待时间
- `MAX_BATCH_DOMAINS` 是 Bot 一次批量允许的最大域名数

## 支持命令

- `/start`
- `/help`
- `/query <domain> [country]`
- `/batch <domain1> <domain2> ...`
- `/history`

## 示例

单域名：

```text
/query example.com
/query example.com us
```

批量：

```text
/batch example.com google.com github.com
```

## 与 API 的关系

- API 负责鉴权
- API 负责 Cookie 缓存
- API 负责结果缓存
- API 负责单域名同步查询，以及异步任务调度和状态查询
- Bot 只负责把 Telegram 命令转成 API 请求
