# Telegram Bot

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

注意：

- `python bot/main.py` 不是正确入口
- 正确入口是 `python -m bot.main`

## Bot 配置

编辑 `bot/config.py`：

```python
TELEGRAM_BOT_TOKEN = "your-bot-token"
API_BASE_URL = "http://localhost:8000"
DEFAULT_COUNTRY = "us"
POLL_INTERVAL = 2
QUERY_TIMEOUT = 60
MAX_BATCH_DOMAINS = 20
```

## 命令

- `/start`
- `/help`
- `/query <domain> [country]`
- `/batch <domain1> <domain2> ...`
- `/history`

## 和缓存的关系

- Bot 本身不存结果
- Bot 通过 API 查询
- 是否命中缓存由 API 决定
- 相同 `domain + country` 再次查询时，API 会优先返回 SQLite 缓存

## 常见问题

### 为什么第一次慢，后面快一些

第一次可能同时发生：

- Cookie 刷新
- 实时查询 Ahrefs
- 结果写入 SQLite

后续相同域名查询通常只需要：

- 请求 API
- 读取 SQLite 缓存
- 返回结果

### 为什么批量查询还会触发实时请求

因为缓存是按单个域名存的，不是按整条 batch 存的。

例如只缓存过：

```text
example.com
```

执行：

```text
/batch example.com google.com github.com
```

则：

- `example.com` 命中缓存
- `google.com` 实时查询
- `github.com` 实时查询
