# Ahrefs DR 批量查询 Telegram Bot 文档

## 概述

Telegram Bot 提供便捷的域名 DR 和 AR 查询服务，通过聊天界面即可快速查询。

**版本**: v2.2.0

## 功能特性

- ✅ 单域名查询
- ✅ 批量查询（最多 10 个域名）
- ✅ 查询历史记录
- ✅ Markdown 格式化输出
- ✅ 实时进度提示
- ✅ 错误处理和友好提示
- ✅ 自动域名格式清理

## 快速开始

### 1. 创建 Telegram Bot

1. 在 Telegram 中搜索 `@BotFather`
2. 发送 `/newbot` 创建新机器人
3. 按提示设置机器人名称和用户名
4. 获取 Bot Token（格式：`123456789:ABCdefGHIjklMNOpqrsTUVwxyz`）

### 2. 配置 Bot Token

**方式 1: 环境变量（推荐）**

```bash
# Windows
set TELEGRAM_BOT_TOKEN=你的Bot Token

# Linux/Mac
export TELEGRAM_BOT_TOKEN=你的Bot Token
```

**方式 2: 配置文件**

编辑 `bot/config.py`：

```python
TELEGRAM_BOT_TOKEN = "你的Bot Token"
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 启动服务

**启动 API 服务（必需）**

```bash
# 终端 1: 启动 API 服务
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

**启动 Bot**

```bash
# 终端 2: 启动 Bot
python bot/main.py
```

### 5. 使用 Bot

在 Telegram 中搜索你的 Bot 用户名，发送 `/start` 开始使用。

## 命令说明

### /start

显示欢迎消息和快速入门指南。

**示例：**
```
/start
```

### /query

查询单个域名的 DR 和 AR。

**语法：**
```
/query <域名> [国家代码]
```

**示例：**
```
/query example.com
/query example.com us
/query https://example.com
```

**响应示例：**
```
✅ example.com

⭐ DR: 93.0
📊 AR: 120
```

### /batch

批量查询多个域名（最多 10 个）。

**语法：**
```
/batch <域名1> <域名2> <域名3> ...
```

**示例：**
```
/batch example.com google.com
/batch example.com google.com github.com
```

**响应示例：**
```
📊 批量查询结果

总计: 3 | 成功: 3 | 失败: 0

──────────────────────────────
✅ example.com

⭐ DR: 93.0
📊 AR: 120
──────────────────────────────
✅ google.com

⭐ DR: 99.0
📊 AR: 3
──────────────────────────────
✅ github.com

⭐ DR: 96.0
📊 AR: 19
```

### /history

查看最近的查询历史（最多 10 条）。

**示例：**
```
/history
```

**响应示例：**
```
📝 查询历史 (最近 3 条)

1. ✅ 1 个域名 - 2026-03-30 03:06:08
2. ✅ 3 个域名 - 2026-03-30 03:10:15
3. ⏳ 5 个域名 - 2026-03-30 03:15:20
```

### /help

显示帮助信息和命令说明。

**示例：**
```
/help
```

## 配置选项

编辑 `bot/config.py` 自定义配置：

```python
# Bot Token
TELEGRAM_BOT_TOKEN = "你的Bot Token"

# 管理员用户 ID（可选）
TELEGRAM_ADMIN_IDS = [
    123456789,  # 替换为你的 Telegram User ID
]

# API 服务地址
API_BASE_URL = "http://localhost:8000"

# 默认国家代码
DEFAULT_COUNTRY = "us"

# 查询结果轮询间隔（秒）
POLL_INTERVAL = 2

# 查询超时时间（秒）
QUERY_TIMEOUT = 60

# 批量查询最大域名数量
MAX_BATCH_DOMAINS = 10
```

## 国家代码

支持的国家代码（部分）：

| 代码 | 国家 |
|------|------|
| us | 美国 |
| br | 巴西 |
| uk | 英国 |
| de | 德国 |
| fr | 法国 |
| jp | 日本 |
| cn | 中国 |
| in | 印度 |
| au | 澳大利亚 |
| ca | 加拿大 |

完整列表请参考 Ahrefs 官方文档。

## 使用示例

### 场景 1: 快速查询单个域名

```
用户: /query example.com

Bot: 🔍 正在查询 example.com...

Bot: ✅ example.com

⭐ DR: 93.0
📊 AR: 120
```

### 场景 2: 批量查询竞品域名

```
用户: /batch competitor1.com competitor2.com competitor3.com

Bot: 🔍 正在批量查询 3 个域名...

Bot: 📊 批量查询结果

总计: 3 | 成功: 3 | 失败: 0

[结果列表...]
```

### 场景 3: 查看历史记录

```
用户: /history

Bot: 📝 查询历史 (最近 5 条)

1. ✅ 1 个域名 - 2026-03-30 03:06:08
2. ✅ 3 个域名 - 2026-03-30 03:10:15
...
```

## 错误处理

### 常见错误

**未配置 Bot Token**
```
错误: 未配置 TELEGRAM_BOT_TOKEN
请设置环境变量或在 bot/config.py 中配置
```

**解决**: 按照"配置 Bot Token"步骤设置 Token

**API 服务未启动**
```
❌ 查询失败，请稍后重试
```

**解决**: 确保 API 服务正在运行（`python -m uvicorn api.main:app`）

**查询超时**
```
❌ 错误：查询超时
```

**解决**:
- 检查网络连接
- 检查 HubStudio 配置
- 增加 `QUERY_TIMEOUT` 配置值

**域名格式错误**
```
❌ 请提供域名

使用方法：/query example.com
```

**解决**: 按照正确格式输入域名

## 架构说明

```
┌─────────────────────────────────────────────────────────┐
│                    Telegram Bot                         │
│                   (bot/main.py)                         │
└────────────┬────────────────────────────┬───────────────┘
             │                            │
             ▼                            ▼
┌────────────────────────┐   ┌────────────────────────────┐
│   Command Handlers     │   │   API Client               │
│   (bot/handlers.py)    │──▶│   (bot/api_client.py)      │
│                        │   │                            │
│  • /start              │   │  • query_domain()          │
│  • /query              │   │  • batch_query()           │
│  • /batch              │   │  • get_task_result()       │
│  • /history            │   │  • list_tasks()            │
│  • /help               │   │                            │
└────────────────────────┘   └────────────┬───────────────┘
                                          │
                                          ▼
                             ┌────────────────────────────┐
                             │   FastAPI Service          │
                             │   (api/main.py)            │
                             │   http://localhost:8000    │
                             └────────────────────────────┘
```

## 工作流程

### 单域名查询流程

1. 用户发送 `/query example.com`
2. Bot 解析命令和参数
3. 清理域名格式（移除 http://、www. 等）
4. 调用 API 创建查询任务
5. 获取 task_id
6. 轮询查询任务状态（每 2 秒）
7. 任务完成后获取结果
8. 格式化结果为 Markdown
9. 发送给用户

### 批量查询流程

1. 用户发送 `/batch domain1.com domain2.com`
2. Bot 解析域名列表（最多 10 个）
3. 清理所有域名格式
4. 调用 API 创建批量查询任务
5. 轮询任务状态
6. 任务完成后获取所有结果
7. 格式化为统一消息
8. 如果消息过长，分段发送

## 性能指标

- **响应时间**: 3-5 秒/域名
- **批量查询**: 2.5 秒/域名（并行处理）
- **轮询间隔**: 2 秒
- **超时时间**: 60 秒（单域名）
- **最大并发**: 取决于 API 服务配置

## 安全建议

### 1. 保护 Bot Token

- ✅ 使用环境变量存储 Token
- ✅ 不要将 Token 提交到 Git
- ✅ 定期更换 Token
- ❌ 不要在代码中硬编码 Token

### 2. 权限控制

在 `bot/config.py` 中配置管理员 ID：

```python
TELEGRAM_ADMIN_IDS = [123456789]
```

可以在 handlers.py 中添加权限检查：

```python
def is_admin(user_id: int) -> bool:
    return user_id in TELEGRAM_ADMIN_IDS

async def admin_only_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ 此命令仅限管理员使用")
        return
    # 执行管理员命令
```

### 3. 限流保护

建议在 API 服务层实现限流，避免滥用。

## 部署

### 开发环境

```bash
# 启动 API 服务
python -m uvicorn api.main:app --reload

# 启动 Bot
python bot/main.py
```

### 生产环境

**使用 systemd（Linux）**

创建 `/etc/systemd/system/ahrefs-bot.service`：

```ini
[Unit]
Description=Ahrefs Telegram Bot
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/ahrefs
Environment="TELEGRAM_BOT_TOKEN=your-token"
ExecStart=/usr/bin/python3 bot/main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl enable ahrefs-bot
sudo systemctl start ahrefs-bot
sudo systemctl status ahrefs-bot
```

**使用 Docker**

创建 `Dockerfile.bot`：

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "bot/main.py"]
```

构建和运行：

```bash
docker build -f Dockerfile.bot -t ahrefs-bot .
docker run -d --name ahrefs-bot \
  -e TELEGRAM_BOT_TOKEN=your-token \
  -e API_BASE_URL=http://api:8000 \
  ahrefs-bot
```

## 故障排查

### Bot 无响应

1. 检查 Bot Token 是否正确
2. 检查网络连接
3. 查看控制台错误日志
4. 确认 Bot 进程正在运行

### 查询失败

1. 检查 API 服务是否运行
2. 检查 API_BASE_URL 配置
3. 测试 API 健康检查：`curl http://localhost:8000/health`
4. 查看 API 服务日志

### 消息格式错误

1. 检查 Markdown 语法
2. 确认特殊字符已转义
3. 测试消息长度限制

## 下一步计划

- [ ] 内联查询支持（@bot_name domain.com）
- [ ] 用户查询配额管理
- [ ] 查询结果缓存
- [ ] 定时推送功能
- [ ] 数据统计和报表
- [ ] 多语言支持

## 相关文档

- [API.md](API.md) - API 服务文档
- [README.md](README.md) - 项目主文档
- [CHANGELOG.md](CHANGELOG.md) - 更新日志

---

**版本**: v2.2.0
**更新日期**: 2026-03-30
**状态**: ✅ 生产就绪
