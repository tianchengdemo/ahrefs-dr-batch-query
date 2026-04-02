# 快速开始

## 1. 安装依赖

```powershell
cd D:\DEV\ahrefs
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 2. 配置 `config.py`

复制 `config.example.py` 为 `config.py`，填写：

```python
HUBSTUDIO_API_BASE = "http://127.0.0.1:6873"
HUBSTUDIO_CDP_HOST = "127.0.0.1"
APP_ID = "your-app-id"
APP_SECRET = "your-app-secret"
CONTAINER_CODE = "your-container-code"
API_AUTH_ENABLED = True
API_KEYS = ["replace-with-a-long-random-key"]
```

如果使用 Docker 连接宿主机上的 HubStudio：

```python
HUBSTUDIO_API_BASE = "http://host.docker.internal:6873"
HUBSTUDIO_CDP_HOST = "host.docker.internal"
```

## 3. 启动 API

```powershell
.\.venv\Scripts\python.exe -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

检查：

```powershell
curl.exe http://127.0.0.1:8000/health
```

## 4. 启动 Bot

```powershell
.\.venv\Scripts\python.exe -m bot.main
```

## 5. 测试命令

在 Telegram 里发送：

```text
/start
/query example.com
/batch example.com google.com github.com
```

## 6. 使用线上 API

当前生产地址：

```text
https://dr.lookav.net
```

鉴权头：

```text
X-API-Key: your-api-key
```

说明：

- 当前 API 的 `DR/AR` 查询是全局域名指标
- 即使传不同 `country`，这两个字段也不应被当成国家维度数据
- 单域名 `POST /api/query` 默认同步返回实时结果；如需异步可传 `async_mode = true`

## 缓存规则

- Cookie 默认复用 `30` 分钟
- 查询结果默认缓存 `30` 天
- 批量查询只会实时请求未命中的域名
- 相同 `domain` 会优先命中缓存
- Redis 只做热点缓存，SQLite 负责持久化

## 常见现象

### 为什么第一次查询比较慢

因为第一次可能需要：

- 从 HubStudio 获取 Cookie
- 实时请求 Ahrefs
- 把结果写入 SQLite
- 把热点结果写入 Redis

### 为什么第二次 batch 不一定完全秒回

因为缓存是按单个域名保存，不是按整组 batch 保存。

例如只缓存过 `example.com`，再执行：

```text
/batch example.com google.com github.com
```

那么只会命中 `example.com`，其余域名仍然需要实时查询。
