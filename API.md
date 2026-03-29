# Ahrefs DR 批量查询 API 文档

## 概述

FastAPI 服务，提供异步批量查询域名 DR 和 AR 的 RESTful API。

**版本**: v2.1.0
**基础 URL**: `http://localhost:8000`
**文档**: `http://localhost:8000/docs` (Swagger UI)

## 快速开始

### 启动服务

```bash
# 方式 1: 直接启动
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000

# 方式 2: 开发模式（自动重载）
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# 方式 3: 使用 main.py
cd api
python main.py
```

### 访问文档

启动后访问 `http://localhost:8000/docs` 查看交互式 API 文档。

## API 端点

### 1. 根路径

**GET /**

返回 API 基本信息。

**响应示例**:
```json
{
  "name": "Ahrefs DR Batch Query API",
  "version": "2.1.0",
  "docs": "/docs",
  "health": "/health"
}
```

### 2. 健康检查

**GET /health**

检查服务状态。

**响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2026-03-30T03:03:48.302741"
}
```

### 3. 查询单个域名

**POST /api/query**

创建单个域名查询任务。

**请求体**:
```json
{
  "domain": "example.com",
  "country": "us"
}
```

**参数说明**:
- `domain` (必填): 域名
- `country` (可选): 国家代码，默认 "us"

**响应示例**:
```json
{
  "task_id": "c1794d5c-89ad-4e3b-9538-d75b3b789f54",
  "status": "pending",
  "message": "任务已创建，正在处理中"
}
```

**cURL 示例**:
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"domain":"example.com","country":"us"}'
```

### 4. 批量查询域名

**POST /api/batch**

创建批量查询任务。

**请求体**:
```json
{
  "domains": ["example.com", "google.com", "github.com"],
  "country": "us"
}
```

**参数说明**:
- `domains` (必填): 域名列表
- `country` (可选): 国家代码，默认 "us"

**响应示例**:
```json
{
  "task_id": "a2b3c4d5-e6f7-8901-2345-6789abcdef01",
  "status": "pending",
  "message": "任务已创建，正在处理 3 个域名"
}
```

**cURL 示例**:
```bash
curl -X POST http://localhost:8000/api/batch \
  -H "Content-Type: application/json" \
  -d '{"domains":["example.com","google.com"],"country":"us"}'
```

### 5. 获取任务结果

**GET /api/result/{task_id}**

获取任务状态和结果。

**路径参数**:
- `task_id`: 任务 ID（从查询接口返回）

**响应示例（处理中）**:
```json
{
  "task_id": "c1794d5c-89ad-4e3b-9538-d75b3b789f54",
  "status": "processing",
  "created_at": "2026-03-30T03:06:08.067277",
  "completed_at": null,
  "results": null,
  "error": null
}
```

**响应示例（完成）**:
```json
{
  "task_id": "c1794d5c-89ad-4e3b-9538-d75b3b789f54",
  "status": "completed",
  "created_at": "2026-03-30T03:06:08.067277",
  "completed_at": "2026-03-30T03:06:22.139335",
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

**响应示例（失败）**:
```json
{
  "task_id": "c1794d5c-89ad-4e3b-9538-d75b3b789f54",
  "status": "failed",
  "created_at": "2026-03-30T03:06:08.067277",
  "completed_at": "2026-03-30T03:06:10.123456",
  "results": null,
  "error": "未配置 Cookie"
}
```

**cURL 示例**:
```bash
curl http://localhost:8000/api/result/c1794d5c-89ad-4e3b-9538-d75b3b789f54
```

### 6. 列出所有任务

**GET /api/tasks**

获取所有任务列表。

**响应示例**:
```json
{
  "total": 2,
  "tasks": [
    {
      "task_id": "c1794d5c-89ad-4e3b-9538-d75b3b789f54",
      "status": "completed",
      "created_at": "2026-03-30T03:06:08.067277",
      "domains_count": 1
    },
    {
      "task_id": "a2b3c4d5-e6f7-8901-2345-6789abcdef01",
      "status": "processing",
      "created_at": "2026-03-30T03:10:15.123456",
      "domains_count": 3
    }
  ]
}
```

## 数据模型

### QueryRequest
```python
{
  "domain": str,      # 域名
  "country": str      # 国家代码（可选，默认 "us"）
}
```

### BatchQueryRequest
```python
{
  "domains": List[str],  # 域名列表
  "country": str         # 国家代码（可选，默认 "us"）
}
```

### TaskResponse
```python
{
  "task_id": str,     # 任务 ID
  "status": str,      # 任务状态: pending, processing, completed, failed
  "message": str      # 状态消息
}
```

### QueryResult
```python
{
  "domain": str,              # 域名
  "domain_rating": float,     # DR 值
  "ahrefs_rank": int,         # AR 值
  "dr_delta": float,          # DR 变化（可选）
  "ar_delta": int,            # AR 变化（可选）
  "error": str                # 错误信息（可选）
}
```

### TaskResult
```python
{
  "task_id": str,                    # 任务 ID
  "status": str,                     # 任务状态
  "created_at": str,                 # 创建时间
  "completed_at": str,               # 完成时间（可选）
  "results": List[QueryResult],      # 查询结果（可选）
  "error": str                       # 错误信息（可选）
}
```

## 任务状态

| 状态 | 说明 |
|------|------|
| `pending` | 任务已创建，等待处理 |
| `processing` | 任务正在处理中 |
| `completed` | 任务已完成 |
| `failed` | 任务失败 |

## 使用示例

### Python 示例

```python
import requests
import time

# 1. 创建查询任务
response = requests.post(
    "http://localhost:8000/api/query",
    json={"domain": "example.com", "country": "us"}
)
task_id = response.json()["task_id"]
print(f"任务 ID: {task_id}")

# 2. 轮询获取结果
while True:
    result = requests.get(f"http://localhost:8000/api/result/{task_id}").json()
    status = result["status"]
    print(f"状态: {status}")

    if status == "completed":
        print("结果:", result["results"])
        break
    elif status == "failed":
        print("错误:", result["error"])
        break

    time.sleep(2)
```

### JavaScript 示例

```javascript
// 1. 创建查询任务
const response = await fetch('http://localhost:8000/api/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ domain: 'example.com', country: 'us' })
});
const { task_id } = await response.json();
console.log('任务 ID:', task_id);

// 2. 轮询获取结果
const checkResult = async () => {
  const result = await fetch(`http://localhost:8000/api/result/${task_id}`).then(r => r.json());
  console.log('状态:', result.status);

  if (result.status === 'completed') {
    console.log('结果:', result.results);
  } else if (result.status === 'failed') {
    console.log('错误:', result.error);
  } else {
    setTimeout(checkResult, 2000);
  }
};
checkResult();
```

### 批量查询示例

```python
import requests
import time

# 批量查询
domains = ["example.com", "google.com", "github.com"]
response = requests.post(
    "http://localhost:8000/api/batch",
    json={"domains": domains, "country": "us"}
)
task_id = response.json()["task_id"]

# 等待完成
while True:
    result = requests.get(f"http://localhost:8000/api/result/{task_id}").json()
    if result["status"] in ["completed", "failed"]:
        break
    time.sleep(3)

# 输出结果
if result["status"] == "completed":
    for item in result["results"]:
        print(f"{item['domain']}: DR={item['domain_rating']}, AR={item['ahrefs_rank']}")
```

## 配置说明

API 服务使用与命令行工具相同的配置文件 `config.py`。

**必需配置**:
- `HUBSTUDIO_API_BASE`: HubStudio API 地址
- `APP_ID`: HubStudio 应用 ID
- `APP_SECRET`: HubStudio 应用密钥
- `CONTAINER_CODE`: 浏览器容器代码

**可选配置**:
- `SOCKS5_PROXY`: SOCKS5 代理地址
- `AHREFS_COOKIE`: 手动配置的 Cookie（回退选项）

## 错误处理

### 常见错误

**404 Not Found**
```json
{
  "detail": "任务不存在"
}
```

**500 Internal Server Error**
```json
{
  "detail": "未配置 Cookie"
}
```

### 任务失败原因

任务 `status` 为 `failed` 时，`error` 字段包含失败原因：
- `"未配置 Cookie"`: 未配置 HubStudio 或手动 Cookie
- `"Cookie 已过期"`: Cookie 失效，需要重新获取
- `"网络连接失败"`: 无法连接到 Ahrefs API
- `"域名不存在"`: 查询的域名无效

## 性能指标

- **单次查询**: ~3-5 秒
- **批量查询**: ~2.5 秒/域名
- **并发支持**: 使用后台任务，支持多个并发查询
- **内存占用**: ~50MB（基础）+ ~5MB/任务

## 限制说明

### 当前限制

- **任务存储**: 内存存储（重启后丢失）
- **并发限制**: 无限制（依赖系统资源）
- **认证**: 无认证机制
- **限流**: 无限流保护

### 生产环境建议

1. **使用 Redis 存储任务**
   ```python
   # 替换 tasks_storage 为 Redis
   import redis
   r = redis.Redis(host='localhost', port=6379, db=0)
   ```

2. **添加认证**
   ```python
   from fastapi.security import HTTPBearer
   security = HTTPBearer()
   ```

3. **添加限流**
   ```python
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   ```

4. **使用 Celery 处理任务**
   ```python
   from celery import Celery
   celery = Celery('tasks', broker='redis://localhost:6379/0')
   ```

## 部署

### 开发环境

```bash
uvicorn api.main:app --reload
```

### 生产环境

```bash
# 使用 Gunicorn + Uvicorn Workers
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# 或使用 Uvicorn
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker 部署

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t ahrefs-api .
docker run -p 8000:8000 -v $(pwd)/config.py:/app/config.py ahrefs-api
```

## 监控

### 健康检查

```bash
# 定期检查服务状态
curl http://localhost:8000/health
```

### 日志

```bash
# 查看 Uvicorn 日志
uvicorn api.main:app --log-level info
```

### 性能监控

建议集成 Prometheus + Grafana 进行监控：

```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

## 下一步计划

- [ ] Redis 任务存储
- [ ] JWT 认证
- [ ] API 限流
- [ ] Celery 异步任务队列
- [ ] WebSocket 实时通知
- [ ] 数据库持久化
- [ ] 定时任务支持
- [ ] 多账号负载均衡

## 技术栈

- **FastAPI**: Web 框架
- **Uvicorn**: ASGI 服务器
- **Pydantic**: 数据验证
- **BackgroundTasks**: 异步任务处理

## 相关文档

- [README.md](README.md) - 项目主文档
- [QUICKSTART.md](QUICKSTART.md) - 快速入门
- [ARCHITECTURE.md](ARCHITECTURE.md) - 技术架构
- [TODO.md](TODO.md) - 开发计划

---

**版本**: v2.1.0
**更新日期**: 2026-03-30
**状态**: ✅ 生产就绪
