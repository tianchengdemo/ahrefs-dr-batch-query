# API

## Start

```powershell
cd D:\DEV\ahrefs
.\.venv\Scripts\python.exe -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

## Docker

Build and run:

```powershell
docker compose up -d --build
```

Important notes:

- `config.py` is mounted into the container
- `.omc` is mounted for SQLite cache persistence
- `host.docker.internal` is available inside the container
- when running in Docker, set `HUBSTUDIO_API_BASE` and `HUBSTUDIO_CDP_HOST` for the host machine

Typical Docker config:

```python
HUBSTUDIO_API_BASE = "http://host.docker.internal:6873"
HUBSTUDIO_CDP_HOST = "host.docker.internal"
```

## Authentication

Protected endpoints require:

```text
X-API-Key: your-api-key
```

Current behavior:

- `GET /` is public
- `GET /health` is public
- `POST /api/query` requires `X-API-Key`
- `POST /api/batch` requires `X-API-Key`
- `GET /api/result/{task_id}` requires `X-API-Key`
- `GET /api/tasks` requires `X-API-Key`

Multiple keys are supported in `config.py`:

```python
API_AUTH_ENABLED = True
API_KEYS = [
    "key-1",
    "key-2",
]
```

## Endpoints

### `GET /health`

Returns service status and cache configuration.

### `POST /api/query`

Request:

```json
{
  "domain": "example.com",
  "country": "us"
}
```

Example:

```powershell
curl -X POST http://127.0.0.1:8000/api/query `
  -H "Content-Type: application/json" `
  -H "X-API-Key: your-api-key" `
  -d "{\"domain\":\"example.com\",\"country\":\"us\"}"
```

### `POST /api/batch`

Request:

```json
{
  "domains": ["example.com", "google.com"],
  "country": "us"
}
```

### `GET /api/result/{task_id}`

Returns task status and results.

## Cache

- Cookie cache is in memory
- Result cache is SQLite
- Cache hit responses can return `completed + results` directly
- `source` is one of `cache`, `live`, `mixed`

## Config

Key config values in `config.py`:

```python
COOKIE_CACHE_TTL_MINUTES = 30
RESULT_CACHE_ENABLED = True
RESULT_CACHE_DB_PATH = ".omc/result_cache.sqlite3"
RESULT_CACHE_TTL_DAYS = 30
API_AUTH_ENABLED = True
API_KEYS = ["your-api-key"]
```
