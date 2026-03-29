# 待完成计划

## 当前版本

**v2.0.0** - 2026-03-30

## 待完成功能

### 🔥 高优先级

#### 1. API 服务化

**目标**: 将工具封装为 RESTful API 服务

**功能需求**:
- [ ] FastAPI 框架搭建
- [ ] API 端点设计
  - `POST /api/query` - 查询单个域名
  - `POST /api/batch` - 批量查询
  - `GET /api/status` - 查询任务状态
  - `GET /api/history` - 查询历史记录
- [ ] 异步任务队列（Celery + Redis）
- [ ] 结果缓存机制
- [ ] API 认证（JWT Token）
- [ ] 请求限流
- [ ] API 文档（Swagger UI）

**技术栈**:
- FastAPI
- Celery
- Redis
- SQLite/PostgreSQL

**预期时间**: 3-5 天

**API 设计示例**:
```python
# 查询单个域名
POST /api/query
{
  "domain": "example.com",
  "country": "us"
}

# 响应
{
  "task_id": "abc123",
  "status": "processing"
}

# 获取结果
GET /api/result/{task_id}
{
  "status": "completed",
  "data": {
    "domain": "example.com",
    "dr": 93.0,
    "ar": 120
  }
}
```

#### 2. Telegram 机器人集成

**目标**: 通过 Telegram 机器人提供查询服务

**功能需求**:
- [ ] python-telegram-bot 集成
- [ ] 命令设计
  - `/start` - 欢迎消息
  - `/query <domain>` - 查询单个域名
  - `/batch <domains>` - 批量查询（逗号分隔）
  - `/history` - 查询历史
  - `/help` - 帮助信息
- [ ] 内联查询支持
- [ ] 结果格式化（Markdown）
- [ ] 进度通知
- [ ] 错误处理
- [ ] 用户权限管理

**技术栈**:
- python-telegram-bot
- asyncio

**预期时间**: 2-3 天

**使用示例**:
```
用户: /query example.com
机器人: 🔍 正在查询 example.com...

机器人: ✅ 查询完成！
📊 域名: example.com
⭐ DR: 93.0
📈 AR: 120
🔄 DR 变化: 0.0
```

### 📋 中优先级

#### 3. Web UI 界面

**功能需求**:
- [ ] 前端框架（React/Vue）
- [ ] 查询表单
- [ ] 结果展示（表格/图表）
- [ ] 历史记录
- [ ] 数据导出
- [ ] 响应式设计

**预期时间**: 5-7 天

#### 4. 数据库存储

**功能需求**:
- [ ] 数据库设计（SQLite/PostgreSQL）
- [ ] 查询历史存储
- [ ] 结果缓存
- [ ] 数据统计
- [ ] 定期清理

**预期时间**: 2-3 天

#### 5. 定时任务

**功能需求**:
- [ ] 定时查询配置
- [ ] Cron 表达式支持
- [ ] 结果对比
- [ ] 变化告警
- [ ] 邮件通知

**预期时间**: 2-3 天

### 🔧 低优先级

#### 6. Docker 容器化

**功能需求**:
- [ ] Dockerfile 编写
- [ ] docker-compose.yml
- [ ] 环境变量配置
- [ ] 一键部署

**预期时间**: 1-2 天

#### 7. 多账号支持

**功能需求**:
- [ ] 账号管理
- [ ] 自动切换
- [ ] 负载均衡
- [ ] 限流保护

**预期时间**: 2-3 天

#### 8. 数据可视化

**功能需求**:
- [ ] DR 趋势图
- [ ] AR 变化图
- [ ] 对比分析
- [ ] 报表生成

**预期时间**: 3-4 天

## 技术方案

### API 服务架构

```
┌─────────────────────────────────────────────────────────┐
│                     API Gateway                         │
│                    (FastAPI)                            │
└────────────┬────────────────────────────┬───────────────┘
             │                            │
             ▼                            ▼
┌────────────────────────┐   ┌────────────────────────────┐
│   Task Queue           │   │   Database                 │
│   (Celery + Redis)     │   │   (PostgreSQL)             │
└────────────┬───────────┘   └────────────────────────────┘
             │
             ▼
┌────────────────────────┐
│   Worker               │
│   (Ahrefs Client)      │
└────────────────────────┘
```

### Telegram Bot 架构

```
┌─────────────────────────────────────────────────────────┐
│                  Telegram Bot                           │
│              (python-telegram-bot)                      │
└────────────┬────────────────────────────┬───────────────┘
             │                            │
             ▼                            ▼
┌────────────────────────┐   ┌────────────────────────────┐
│   Command Handlers     │   │   Inline Query Handler     │
└────────────┬───────────┘   └────────────────────────────┘
             │
             ▼
┌────────────────────────┐
│   API Client           │
│   (调用 API 服务)       │
└────────────────────────┘
```

## 开发计划

### Phase 1: API 服务化（Week 1）

**Day 1-2**: FastAPI 基础框架
- 项目结构搭建
- API 端点实现
- 请求验证

**Day 3-4**: 异步任务队列
- Celery 集成
- Redis 配置
- 任务调度

**Day 5**: 测试和文档
- API 测试
- Swagger 文档
- 部署脚本

### Phase 2: Telegram Bot（Week 2）

**Day 1-2**: Bot 基础功能
- 命令处理
- 消息格式化
- 错误处理

**Day 3**: 高级功能
- 内联查询
- 进度通知
- 权限管理

**Day 4-5**: 集成测试
- 端到端测试
- 性能优化
- 文档完善

### Phase 3: 数据库和定时任务（Week 3）

**Day 1-2**: 数据库设计
- 表结构设计
- ORM 集成
- 数据迁移

**Day 3-4**: 定时任务
- Cron 配置
- 任务调度
- 结果对比

**Day 5**: 测试和优化
- 性能测试
- 数据清理
- 监控告警

## 依赖更新

### 新增依赖

```txt
# API 服务
fastapi
uvicorn[standard]
celery
redis
python-multipart

# Telegram Bot
python-telegram-bot

# 数据库
sqlalchemy
alembic
psycopg2-binary

# 工具
pydantic
python-dotenv
```

## 配置示例

### API 服务配置

```python
# api_config.py
API_HOST = "0.0.0.0"
API_PORT = 8000
API_SECRET_KEY = "your-secret-key"

REDIS_HOST = "localhost"
REDIS_PORT = 6379

DATABASE_URL = "postgresql://user:pass@localhost/ahrefs"
```

### Telegram Bot 配置

```python
# bot_config.py
TELEGRAM_BOT_TOKEN = "your-bot-token"
TELEGRAM_ADMIN_IDS = [123456789]
```

## 测试计划

### API 测试

- [ ] 单元测试
- [ ] 集成测试
- [ ] 性能测试
- [ ] 压力测试

### Bot 测试

- [ ] 命令测试
- [ ] 并发测试
- [ ] 错误处理测试

## 部署计划

### 开发环境

```bash
# 启动 API 服务
uvicorn api.main:app --reload

# 启动 Celery Worker
celery -A api.tasks worker --loglevel=info

# 启动 Telegram Bot
python bot/main.py
```

### 生产环境

```bash
# Docker Compose
docker-compose up -d
```

## 文档计划

- [ ] API 文档（Swagger）
- [ ] Bot 使用指南
- [ ] 部署文档
- [ ] 开发者文档

## 里程碑

- **v2.1.0** - API 服务化 ✅
- **v2.2.0** - Telegram Bot 集成 ✅
- **v2.3.0** - 数据库和定时任务 ✅
- **v3.0.0** - Web UI 和完整功能 ✅

## 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支
3. 提交代码
4. 创建 Pull Request

## 联系方式

- GitHub Issues: 提交 Bug 和功能请求
- Discussions: 技术讨论和问答

---

**最后更新**: 2026-03-30

**当前版本**: v2.0.0

**下一版本**: v2.1.0 (API 服务化)
