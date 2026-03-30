# Telegram Bot

## Start Order

Start API first:

```powershell
cd D:\DEV\ahrefs
.\.venv\Scripts\python.exe -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Then start Bot:

```powershell
cd D:\DEV\ahrefs
.\.venv\Scripts\python.exe -m bot.main
```

## Bot Config

Edit `bot/config.py`:

```python
TELEGRAM_BOT_TOKEN = "your-bot-token"
API_BASE_URL = "http://localhost:8000"
API_KEY = "your-api-key"
DEFAULT_COUNTRY = "us"
POLL_INTERVAL = 2
QUERY_TIMEOUT = 60
MAX_BATCH_DOMAINS = 20
```

`API_KEY` must match one of the keys in the API server's `API_KEYS`.

## Commands

- `/start`
- `/help`
- `/query <domain> [country]`
- `/batch <domain1> <domain2> ...`
- `/history`

## Client Behavior

- Bot is only a client
- API is responsible for auth, cache, and query execution
- If API returns `completed + results` directly, Bot will not poll `/api/result`
- If API returns `pending`, Bot will poll until the task completes or times out
