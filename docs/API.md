# API

## 启动

```powershell
cd D:\DEV\ahrefs
.\.venv\Scripts\python.exe -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

## 接口

### `GET /`

返回服务基础信息。

### `GET /health`

返回服务状态和缓存配置。

示例：

```json
{
  "status": "healthy",
  "timestamp": "2026-03-30T22:50:13.877674",
  "result_cache_enabled": true,
  "result_cache_ttl_days": 30,
  "cookie_cache_ttl_minutes": 30
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

返回：

- 未命中缓存时：`status = pending`
- 命中缓存时：`status = completed`

缓存命中示例：

```json
{
  "task_id": "xxxx",
  "status": "completed",
  "message": "Result returned from cache"
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

行为：

- 全部命中缓存时，直接返回 `completed`
- 部分命中缓存时，只实时查询未命中的域名
- 全部未命中时，整批实时查询

### `GET /api/result/{task_id}`

返回任务结果。

示例：

```json
{
  "task_id": "xxxx",
  "status": "completed",
  "created_at": "2026-03-30T22:50:29.139531",
  "completed_at": "2026-03-30T22:50:42.632392",
  "results": [
    {
      "domain": "example.com",
      "domain_rating": 93.0,
      "ahrefs_rank": 120,
      "dr_delta": 0.0,
      "ar_delta": -3,
      "error": null
    }
  ],
  "error": null
}
```

### `GET /api/tasks`

返回当前进程内的任务列表。

## 缓存实现

### Cookie

- HubStudio Cookie 缓存在内存
- 默认 TTL 为 `30` 分钟
- 403 时自动刷新

相关代码：

- [api/main.py](D:/DEV/ahrefs/api/main.py)
- [hubstudio.py](D:/DEV/ahrefs/hubstudio.py)

### 结果

- 使用 SQLite
- 默认数据库路径：`.omc/result_cache.sqlite3`
- 默认 TTL：`30` 天

相关代码：

- [result_cache.py](D:/DEV/ahrefs/result_cache.py)
- [api/main.py](D:/DEV/ahrefs/api/main.py)

## 配置项

在 `config.py` 中：

```python
COOKIE_CACHE_TTL_MINUTES = 30
RESULT_CACHE_ENABLED = True
RESULT_CACHE_DB_PATH = ".omc/result_cache.sqlite3"
RESULT_CACHE_TTL_DAYS = 30
```
