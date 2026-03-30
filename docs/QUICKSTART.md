# Quick Start

## 1. 安装依赖

```powershell
cd D:\DEV\ahrefs
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 2. 配置

复制 `config.example.py` 为 `config.py`，填写：

```python
HUBSTUDIO_API_BASE = "http://127.0.0.1:6873"
APP_ID = "your-app-id"
APP_SECRET = "your-app-secret"
CONTAINER_CODE = "your-container-code"
```

## 3. 启动 API

```powershell
.\.venv\Scripts\python.exe -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

检查：

```powershell
curl http://127.0.0.1:8000/health
```

## 4. 启动 Bot

```powershell
.\.venv\Scripts\python.exe -m bot.main
```

## 5. 测试

Telegram 里发送：

```text
/start
/query example.com
/batch example.com google.com github.com
```

## 缓存规则

- Cookie 默认复用 30 分钟
- 结果默认缓存 30 天
- 批量查询只会实时请求未命中的域名
- 相同 `domain + country` 再次查询会优先走缓存

## 常见现象

### 为什么第一次慢

因为首次可能需要：

- 从 HubStudio 刷新 Cookie
- 请求 Ahrefs
- 写入 SQLite 缓存

### 为什么第二次 batch 还可能不完全秒回

因为缓存按单个域名存储，不按整条 batch 存储。

例如只缓存过 `example.com` 时，执行：

```text
/batch example.com google.com github.com
```

只会命中 `example.com`，其余两个仍然要实时查询。
