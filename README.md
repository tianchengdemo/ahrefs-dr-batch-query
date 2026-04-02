# Ahrefs Query Service

基于 HubStudio 和 Ahrefs 会话的域名查询服务，提供：

- CLI 查询
- FastAPI 接口
- Telegram Bot 客户端
- Cookie 内存缓存
- SQLite 持久化结果缓存
- Redis 热点缓存
- Docker + Caddy 域名反向代理

## 当前状态

当前实现与运行方式：

- API 是核心执行层，负责鉴权、缓存、同步查询和任务轮询
- Bot 只是客户端，不再承载缓存和业务逻辑
- 当前 `/api/query` 和 `/api/batch` 返回的是域名全局 `DR/AR`
- 这两个接口中的 `country` 参数暂时仅保留兼容，不再参与 `DR/AR` 缓存分片
- 单域名 `POST /api/query` 默认同步返回实时结果；如需异步可传 `async_mode = true`
- Cookie 默认在内存中复用 `30` 分钟
- 成功查询结果默认缓存 `30` 天
- Redis 作为热点缓存，SQLite 作为持久化缓存
- `DR/AR` 缓存按 `domain` 复用，不再按 `domain + country` 重复存储
- 获取完 Cookie 后会自动关闭 HubStudio 浏览器
- Docker 部署已支持 Caddy 自动 HTTPS

## 生产地址

- API: `https://dr.lookav.net`
- Swagger: `https://dr.lookav.net/docs`
- 健康检查: `https://dr.lookav.net/health`

## 项目结构

```text
ahrefs/
├─ api/
│  └─ main.py
├─ bot/
│  ├─ api_client.py
│  ├─ config.py
│  ├─ handlers.py
│  └─ main.py
├─ deploy/
│  └─ Caddyfile
├─ docs/
│  ├─ API.md
│  ├─ ARCHITECTURE.md
│  ├─ BOT.md
│  ├─ DOCKER.md
│  └─ QUICKSTART.md
├─ ahrefs.py
├─ config.example.py
├─ docker-compose.yml
├─ hubstudio.py
├─ main.py
└─ result_cache.py
```

## 依赖

- Python 3.10+
- HubStudio Local API
- 已登录 Ahrefs 的 HubStudio 环境
- Docker Desktop 或 Docker Engine（如需容器部署）

安装依赖：

```powershell
cd D:\DEV\ahrefs
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 基础配置

复制 `config.example.py` 为 `config.py`，填写：

```python
HUBSTUDIO_API_BASE = "http://127.0.0.1:6873"
HUBSTUDIO_CDP_HOST = "127.0.0.1"
APP_ID = "your-app-id"
APP_SECRET = "your-app-secret"
CONTAINER_CODE = "your-container-code"
```

缓存与鉴权相关配置：

```python
COOKIE_CACHE_TTL_MINUTES = 30
RESULT_CACHE_ENABLED = True
RESULT_CACHE_DB_PATH = ".omc/result_cache.sqlite3"
RESULT_CACHE_TTL_DAYS = 30
REDIS_ENABLED = False
REDIS_URL = "redis://127.0.0.1:6379/0"
REDIS_CACHE_TTL_SECONDS = 21600
API_AUTH_ENABLED = True
API_KEYS = ["replace-with-a-long-random-key"]
```

## 本地启动 API

```powershell
cd D:\DEV\ahrefs
.\.venv\Scripts\python.exe -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

检查：

```powershell
curl.exe http://127.0.0.1:8000/health
```

## Docker 启动

```powershell
docker compose up -d --build
```

如果要用 Caddy 绑定域名，在根目录创建 `.env`：

```dotenv
CADDY_DOMAIN=dr.lookav.net
```

## Bot 启动

先启动 API，再启动 Bot：

```powershell
cd D:\DEV\ahrefs
.\.venv\Scripts\python.exe -m bot.main
```

## 缓存说明

### Cookie 缓存

- API 在需要实时查询时，才会从 HubStudio 获取 Cookie
- Cookie 在 TTL 内复用，不会每次查询都重启浏览器
- 当 Ahrefs 返回 `403` 时，会自动失效并重新获取 Cookie
- 获取完 Cookie 后会自动关闭 HubStudio 浏览器

### 结果缓存

- 单域名和批量查询都会先查缓存
- 批量查询只会实时请求未命中的域名
- Redis 命中优先返回
- Redis 未命中时会回落到 SQLite
- SQLite 命中后会重新回填 Redis

示例：

```text
/batch example.com google.com github.com
```

如果只有 `example.com` 已缓存，那么这次只会实时请求 `google.com` 和 `github.com`。

注意：

- 当前 `DR/AR` 是域名全局指标，不是国家维度指标
- 如果后续需要国家维度数据，应走新的国家指标接口，而不是复用当前 `DR/AR` 接口

## 文档

- [快速开始](docs/QUICKSTART.md)
- [API 文档](docs/API.md)
- [Bot 文档](docs/BOT.md)
- [Docker 部署](docs/DOCKER.md)
- [架构说明](docs/ARCHITECTURE.md)
