# Files

## 主要文件

| Path | Purpose |
| --- | --- |
| `api/main.py` | FastAPI 入口，包含 Cookie 缓存和结果缓存流程 |
| `bot/main.py` | Telegram Bot 启动入口 |
| `bot/handlers.py` | Bot 命令处理 |
| `bot/api_client.py` | Bot 调用 API 的客户端 |
| `ahrefs.py` | Ahrefs 请求客户端 |
| `hubstudio.py` | HubStudio API 客户端 |
| `result_cache.py` | SQLite 结果缓存 |
| `config.example.py` | 配置示例 |
| `requirements.txt` | Python 依赖 |

## 已删除的无用文件

以下调试或一次性脚本已移除：

- `debug_cookie.py`
- `debug_all_cookies.py`
- `manual_cookie_guide.py`
- `start_browser.py`
- `test_hubstudio.py`
- `test_request.py`

## 运行时生成文件

这些文件不会提交：

- `.omc/result_cache.sqlite3`
- `.omc/*.log`
- `__pycache__/`
