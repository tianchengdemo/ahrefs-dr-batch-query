# 架构说明

## 总览

当前项目分为五层：

1. CLI 层：`main.py`
2. Bot 客户端层：`bot/`
3. API 层：`api/main.py`
4. 缓存层：`result_cache.py`
5. 外部依赖层：HubStudio、Ahrefs、Redis、SQLite、Caddy

## 当前设计原则

- API 是核心入口
- Bot 只是客户端
- 结果缓存优先在 API 层处理
- Cookie 生命周期由 API 层管理
- Docker 部署通过 Caddy 提供 HTTPS

## 模块职责

### `api/main.py`

负责：

- API 路由
- API Key 鉴权
- Cookie 内存缓存
- 单域名同步查询，以及异步任务创建和轮询状态
- 缓存命中判断
- 调用 Ahrefs 查询
- 在需要时从 HubStudio 获取 Cookie
- 获取完 Cookie 后关闭浏览器

公开接口：

- `GET /`
- `GET /health`
- `POST /api/query`
- `POST /api/batch`
- `GET /api/result/{task_id}`
- `GET /api/tasks`

### `result_cache.py`

负责：

- SQLite 持久化缓存
- Redis 热点缓存
- TTL 过期控制
- SQLite 命中后回填 Redis

缓存键维度：

```text
domain
```

### `ahrefs.py`

负责：

- 组装 Ahrefs 请求
- 发送带 Cookie 的会话请求
- 通过代理访问 Ahrefs
- 解析 DR、AR 等结果

### `hubstudio.py`

负责：

- 调用 HubStudio Local API
- 启动浏览器
- 停止浏览器
- 通过 CDP 获取 Cookie
- 回退导出 Cookie
- 读取环境代理配置

### `bot/api_client.py`

负责：

- 调用 API
- 处理 `completed` 或 `pending` 响应
- 仅在 `pending` 时轮询 `/api/result/{task_id}`

### `bot/handlers.py`

负责：

- 解析 Telegram 命令
- 把命令转成 API 调用
- 格式化返回消息

## 请求流程

### 单域名查询

1. Bot 或 CLI 发起查询
2. API 规范化 `domain` 和 `country`
3. API 先查 Redis
4. Redis 未命中时查 SQLite
5. 如果缓存命中，直接返回 `completed`
6. 如果缓存未命中且 `async_mode = false`，同步执行实时查询并直接返回 `completed + results`
7. 如果缓存未命中且 `async_mode = true`，创建后台任务并立即返回 `pending + task_id`
8. API 需要 Cookie 时从 HubStudio 获取
9. 获取完 Cookie 后关闭浏览器
10. 查询结果写入 SQLite，并回填 Redis

### 批量查询

1. API 逐个检查每个域名缓存
2. 已命中域名直接复用缓存
3. 未命中域名走实时查询
4. 返回的 `source` 可能是：

- `cache`
- `live`
- `mixed`

## 鉴权设计

API 鉴权在 `api/main.py` 中统一处理。

规则：

- `GET /` 和 `GET /health` 公开
- 查询类接口要求 `X-API-Key`
- 支持配置多个 API Key

## Docker 部署结构

当前 Docker 结构：

```text
Client -> Caddy -> FastAPI -> Redis / SQLite
                           -> HubStudio(host)
                           -> Ahrefs
```

说明：

- Caddy 处理 HTTPS
- FastAPI 处理业务逻辑
- Redis 提供热点缓存
- SQLite 提供持久化缓存
- HubStudio 仍然在宿主机

## 关键行为

### Cookie 缓存

- 默认缓存 `30` 分钟
- 只有需要实时查询时才会刷新
- 刷新成功后自动关闭 HubStudio 浏览器

### 结果缓存

- 默认缓存 `30` 天
- Redis 只缓存热点数据
- SQLite 是最终持久化来源

### Bot 行为

- Bot 不直接访问 Ahrefs
- Bot 不负责缓存
- Bot 不负责鉴权判断
- Bot 只依赖 API 的返回格式
