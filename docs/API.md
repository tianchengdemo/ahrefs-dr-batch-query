# API

## Base URLs

Production:

```text
https://dr.lookav.net
```

Local:

```text
http://127.0.0.1:8000
```

Swagger:

```text
https://dr.lookav.net/docs
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

## Common Behavior

- Query requests normalize the domain and country before execution.
- Cache hits can return immediately with `status = "completed"` and inline `results`.
- Cache misses return `status = "pending"` with a `task_id`, then finish asynchronously.
- Response `source` is one of `cache`, `live`, `mixed`.
- Batch queries may return part cached and part live.

## Endpoints

### `GET /health`

Returns service status and cache configuration.

Example:

```powershell
curl.exe https://dr.lookav.net/health
```

Typical response:

```json
{
  "status": "healthy",
  "timestamp": "2026-03-30T20:31:20.876890",
  "result_cache_enabled": true,
  "result_cache_ttl_days": 30,
  "cookie_cache_ttl_minutes": 30,
  "redis_enabled": true,
  "redis_cache_ttl_seconds": 21600
}
```

### `POST /api/query`

Request:

```json
{
  "domain": "example.com",
  "country": "us"
}
```

PowerShell example:

```powershell
curl.exe -X POST "https://dr.lookav.net/api/query" `
  -H "Content-Type: application/json" `
  -H "X-API-Key: your-api-key" `
  -d "{\"domain\":\"example.com\",\"country\":\"us\"}"
```

Immediate cache-hit response:

```json
{
  "task_id": "6b76c8f4-4c17-4eab-88f3-c2d1efc37d42",
  "status": "completed",
  "message": "Result returned from cache",
  "results": [
    {
      "domain": "example.com",
      "domain_rating": "79",
      "ahrefs_rank": "12345"
    }
  ],
  "source": "cache",
  "cached_domains": 1,
  "live_domains": 0
}
```

Live-query response:

```json
{
  "task_id": "1e7590dd-6d53-4f8d-8ebc-c6404447b4b5",
  "status": "pending",
  "message": "Task created and processing",
  "source": "live",
  "cached_domains": 0,
  "live_domains": 1
}
```

### `POST /api/batch`

Request:

```json
{
  "domains": ["example.com", "google.com", "github.com"],
  "country": "us"
}
```

PowerShell example:

```powershell
curl.exe -X POST "https://dr.lookav.net/api/batch" `
  -H "Content-Type: application/json" `
  -H "X-API-Key: your-api-key" `
  -d "{\"domains\":[\"example.com\",\"google.com\",\"github.com\"],\"country\":\"us\"}"
```

Typical response:

```json
{
  "task_id": "a4be3a50-b8aa-4b26-bd10-b2bfb67c1775",
  "status": "pending",
  "message": "Task created and processing 3 domains",
  "source": "mixed",
  "cached_domains": 1,
  "live_domains": 2
}
```

### `GET /api/result/{task_id}`

Returns task status and results.

PowerShell example:

```powershell
curl.exe -H "X-API-Key: your-api-key" `
  "https://dr.lookav.net/api/result/a4be3a50-b8aa-4b26-bd10-b2bfb67c1775"
```

Typical response:

```json
{
  "task_id": "a4be3a50-b8aa-4b26-bd10-b2bfb67c1775",
  "status": "completed",
  "created_at": "2026-03-30T20:40:00.000000",
  "completed_at": "2026-03-30T20:40:05.000000",
  "results": [
    {
      "domain": "example.com",
      "domain_rating": "79",
      "ahrefs_rank": "12345"
    }
  ],
  "error": null,
  "source": "mixed",
  "cached_domains": 1,
  "live_domains": 2
}
```

### `GET /api/tasks`

Returns the in-memory task list.

PowerShell example:

```powershell
curl.exe -H "X-API-Key: your-api-key" "https://dr.lookav.net/api/tasks"
```

## Polling Pattern

Recommended client flow:

1. `POST /api/query` or `POST /api/batch`
2. If `status` is `completed`, use `results` directly
3. If `status` is `pending`, poll `GET /api/result/{task_id}`
4. Stop polling when `status` becomes `completed` or `failed`

Python example:

```python
import time
import requests

BASE_URL = "https://dr.lookav.net"
API_KEY = "your-api-key"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json",
}

resp = requests.post(
    f"{BASE_URL}/api/query",
    headers=HEADERS,
    json={"domain": "example.com", "country": "us"},
    timeout=30,
)
resp.raise_for_status()
data = resp.json()

if data["status"] == "completed":
    print(data["results"])
else:
    task_id = data["task_id"]
    while True:
        result = requests.get(
            f"{BASE_URL}/api/result/{task_id}",
            headers={"X-API-Key": API_KEY},
            timeout=30,
        )
        result.raise_for_status()
        payload = result.json()
        if payload["status"] == "completed":
            print(payload["results"])
            break
        time.sleep(2)
```

## Docker Notes

- `config.py` is mounted into the container
- `.omc` is mounted for SQLite cache persistence
- `host.docker.internal` is available inside the container
- Docker Caddy terminates HTTPS for `dr.lookav.net`

Typical Docker config:

```python
HUBSTUDIO_API_BASE = "http://host.docker.internal:6873"
HUBSTUDIO_CDP_HOST = "host.docker.internal"
```

## Cache

- Cookie cache is in memory
- Result cache is persisted in SQLite
- Redis can be enabled as a hot cache in front of SQLite
- SQLite remains the durable source
- Redis hot-cache TTL is currently `21600` seconds
- Result cache TTL is currently `30` days

## Config

Key config values in `config.py`:

```python
COOKIE_CACHE_TTL_MINUTES = 30
RESULT_CACHE_ENABLED = True
RESULT_CACHE_DB_PATH = ".omc/result_cache.sqlite3"
RESULT_CACHE_TTL_DAYS = 30
REDIS_ENABLED = True
REDIS_URL = "redis://redis:6379/0"
REDIS_CACHE_TTL_SECONDS = 21600
API_AUTH_ENABLED = True
API_KEYS = ["your-api-key"]
```
