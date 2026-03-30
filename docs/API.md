# API 文档

## 基础地址

生产环境：

```text
https://dr.lookav.net
```

本地环境：

```text
http://127.0.0.1:8000
```

Swagger 文档：

```text
https://dr.lookav.net/docs
```

## 鉴权方式

受保护接口需要请求头：

```text
X-API-Key: your-api-key
```

当前接口权限规则：

- `GET /` 公开
- `GET /health` 公开
- `POST /api/query` 需要 `X-API-Key`
- `POST /api/batch` 需要 `X-API-Key`
- `GET /api/result/{task_id}` 需要 `X-API-Key`
- `GET /api/tasks` 需要 `X-API-Key`

`config.py` 支持配置多个 key：

```python
API_AUTH_ENABLED = True
API_KEYS = [
    "key-1",
    "key-2",
]
```

## 接口行为说明

- 查询前会先规范化域名和国家代码。
- 命中缓存时，接口会直接返回 `status = "completed"` 和 `results`。
- 未命中缓存时，接口会返回 `status = "pending"` 和 `task_id`，后台异步执行。
- `source` 字段可能是 `cache`、`live`、`mixed`。
- 批量查询可能部分命中缓存、部分实时查询。

## 接口说明

### `GET /health`

返回服务状态和缓存配置。

示例：

```powershell
curl.exe https://dr.lookav.net/health
```

典型返回：

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

请求体：

```json
{
  "domain": "example.com",
  "country": "us"
}
```

PowerShell 示例：

```powershell
curl.exe -X POST "https://dr.lookav.net/api/query" `
  -H "Content-Type: application/json" `
  -H "X-API-Key: your-api-key" `
  -d "{\"domain\":\"example.com\",\"country\":\"us\"}"
```

缓存命中时的即时返回：

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

实时查询时的返回：

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

请求体：

```json
{
  "domains": ["example.com", "google.com", "github.com"],
  "country": "us"
}
```

PowerShell 示例：

```powershell
curl.exe -X POST "https://dr.lookav.net/api/batch" `
  -H "Content-Type: application/json" `
  -H "X-API-Key: your-api-key" `
  -d "{\"domains\":[\"example.com\",\"google.com\",\"github.com\"],\"country\":\"us\"}"
```

典型返回：

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

返回任务状态和结果。

PowerShell 示例：

```powershell
curl.exe -H "X-API-Key: your-api-key" `
  "https://dr.lookav.net/api/result/a4be3a50-b8aa-4b26-bd10-b2bfb67c1775"
```

典型返回：

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

返回当前内存中的任务列表。

PowerShell 示例：

```powershell
curl.exe -H "X-API-Key: your-api-key" "https://dr.lookav.net/api/tasks"
```

## 推荐调用流程

推荐客户端流程：

1. 调用 `POST /api/query` 或 `POST /api/batch`
2. 如果返回 `status = "completed"`，直接使用 `results`
3. 如果返回 `status = "pending"`，使用 `task_id` 轮询 `GET /api/result/{task_id}`
4. 当 `status` 变成 `completed` 或 `failed` 时结束轮询

Python 示例：

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

## Docker 说明

- `config.py` 会挂载进容器
- `.omc` 会挂载出来，用于持久化 SQLite 缓存
- 容器内可通过 `host.docker.internal` 访问宿主机
- Docker 中由 Caddy 为 `dr.lookav.net` 提供 HTTPS

典型 Docker 配置：

```python
HUBSTUDIO_API_BASE = "http://host.docker.internal:6873"
HUBSTUDIO_CDP_HOST = "host.docker.internal"
```

## 缓存说明

- Cookie 缓存保存在内存中
- 查询结果持久化在 SQLite
- Redis 作为热点缓存加速读取
- SQLite 仍然是持久化数据源
- Redis 热点缓存 TTL 当前为 `21600` 秒
- 查询结果缓存 TTL 当前为 `30` 天

## 关键配置

`config.py` 中常用配置：

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
