# 更新日志

所有重要的项目变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [2.1.0] - 2026-03-30

### 新增

- **FastAPI REST API 服务** - 将工具封装为 RESTful API 服务
- **异步任务处理** - 使用 BackgroundTasks 实现异步查询
- **任务状态追踪** - 支持查询任务状态和结果
- **批量查询 API** - 支持通过 API 批量查询多个域名
- **交互式 API 文档** - 自动生成 Swagger UI 文档
- **健康检查端点** - 提供服务健康状态检查
- **CORS 支持** - 支持跨域请求

### API 端点

- `GET /` - API 基本信息
- `GET /health` - 健康检查
- `POST /api/query` - 查询单个域名
- `POST /api/batch` - 批量查询
- `GET /api/result/{task_id}` - 获取任务结果
- `GET /api/tasks` - 列出所有任务

### 技术实现

- FastAPI 框架
- Pydantic 数据验证
- Uvicorn ASGI 服务器
- 后台任务队列
- 内存任务存储

### 文档

- 新增 `API.md` - 完整的 API 使用文档
- 包含使用示例（Python、JavaScript、cURL）
- 部署指南和性能指标

### 依赖

- 新增 `fastapi` - Web 框架
- 新增 `uvicorn[standard]` - ASGI 服务器
- 新增 `pydantic` - 数据验证

### 测试结果

```bash
# 测试查询
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"domain":"example.com","country":"us"}'

# 响应
{
  "task_id": "c1794d5c-89ad-4e3b-9538-d75b3b789f54",
  "status": "pending",
  "message": "任务已创建，正在处理中"
}

# 查询结果
{
  "status": "completed",
  "results": [
    {
      "domain": "example.com",
      "domain_rating": 93.0,
      "ahrefs_rank": 120
    }
  ]
}
```

### 下一步计划

- Redis 任务存储
- JWT 认证
- Celery 异步任务队列
- WebSocket 实时通知

## [2.0.0] - 2026-03-30

### 新增

- **完全自动化 Cookie 获取** - 通过 Chrome DevTools Protocol (CDP) 自动获取所有 Cookie
- **HttpOnly Cookie 支持** - 自动获取 BSSESSID 等 HttpOnly Cookie，无需手动配置
- **智能浏览器管理** - 自动启动/关闭 HubStudio 浏览器，添加必要的 CDP 参数
- **自动页面加载** - 启动时自动打开 app.ahrefs.com 并等待加载完成
- **WebSocket 连接** - 通过 WebSocket 连接浏览器 CDP 端点获取 Cookie
- **三级回退机制** - CDP → HubStudio API → 手动配置，确保稳定性
- **详细日志输出** - 显示 Cookie 获取详情（总数、HttpOnly 数量）

### 修复

- **Windows 控制台编码问题** - 修复中文乱码显示
- **Ahrefs API 响应解析** - 支持新的数组格式响应 `['Ok', {...}]`
- **Cookie 域名匹配** - 改进域名过滤逻辑，支持子域名匹配
- **代理配置获取** - 修复 HubStudio 环境代理自动获取
- **特殊字符处理** - 移除 ✓ ✗ 等特殊字符，避免编码错误

### 变更

- **移除手动 Cookie 配置** - 不再需要在 config.py 中配置 MANUAL_COOKIES
- **简化配置流程** - 只需配置 HubStudio API 凭证即可
- **优化启动流程** - 浏览器重启 + 页面加载 + CDP 连接一气呵成
- **改进错误处理** - 更友好的错误提示和自动回退

### 依赖

- 新增 `websocket-client` - 用于 CDP WebSocket 连接

### 技术细节

#### CDP 集成

```python
# 启动浏览器时添加 CDP 参数
params = {
    "containerCode": 970506927,
    "args": ["--remote-allow-origins=*"],
    "containerTabs": ["https://app.ahrefs.com"]
}

# 通过 WebSocket 获取 Cookie
ws_url = f"ws://127.0.0.1:{debugging_port}/devtools/page/xxx"
command = {"id": 1, "method": "Network.getCookies"}
```

#### Cookie 获取流程

1. 关闭现有浏览器实例
2. 启动浏览器（带 CDP 参数）
3. 打开 app.ahrefs.com
4. 等待页面加载（5秒）
5. 连接 CDP WebSocket
6. 调用 Network.getCookies
7. 过滤 ahrefs.com 域名的 Cookie
8. 包括所有 HttpOnly Cookie

#### 响应格式适配

旧格式：
```json
{
  "result": {
    "data": {
      "domainRating": {"value": 93.0},
      "ahrefsRank": {"value": 120}
    }
  }
}
```

新格式：
```json
[
  "Ok",
  {
    "domainRating": {"value": 93.0},
    "ahrefsRank": {"value": 120}
  }
]
```

## [1.0.0] - 2026-03-21

### 新增

- **HubStudio API 集成** - 通过 HubStudio Local API 管理浏览器环境
- **Cookie 导出** - 从 HubStudio 导出环境 Cookie（不含 HttpOnly）
- **代理自动配置** - 自动读取 HubStudio 环境的 SOCKS5 代理配置
- **批量查询** - 支持查询多个域名的 DR 和 Ahrefs Rank
- **多种输出格式** - 表格、JSON、CSV 三种输出格式
- **国家代码支持** - 支持指定国家代码查询
- **请求重试机制** - 失败自动重试，最多 3 次
- **限流处理** - 429 错误自动等待重试
- **完整概览数据** - 支持获取 UR、反链、流量等完整数据

### 技术实现

- Python 3.10+ 支持
- requests 库处理 HTTP 请求
- pysocks 支持 SOCKS5 代理
- 模块化设计：config.py、hubstudio.py、ahrefs.py、main.py

### 已知问题

- ❌ 无法获取 HttpOnly Cookie（BSSESSID）
- ❌ 需要手动从浏览器复制会话 Cookie
- ❌ Windows 控制台中文显示乱码
- ❌ 响应解析不支持数组格式

---

## 版本说明

### 主版本号 (Major)

当做了不兼容的 API 修改时递增。

### 次版本号 (Minor)

当做了向下兼容的功能性新增时递增。

### 修订号 (Patch)

当做了向下兼容的问题修正时递增。

---

## 路线图

### v2.1.0 (计划中)

- [ ] 支持多账号切换
- [ ] 添加查询历史记录
- [ ] 支持定时批量查询
- [ ] 添加数据可视化
- [ ] 支持更多 Ahrefs 指标

### v2.2.0 (计划中)

- [ ] Web UI 界面
- [ ] 数据库存储
- [ ] API 服务模式
- [ ] Docker 容器化
- [ ] 分布式查询支持

### v3.0.0 (未来)

- [ ] 支持其他 SEO 工具（Semrush、Moz）
- [ ] 竞品分析功能
- [ ] 自动报告生成
- [ ] 邮件通知
- [ ] Webhook 集成

---

## 贡献指南

欢迎提交 Issue 和 Pull Request！

### 提交 Issue

- 使用清晰的标题描述问题
- 提供复现步骤
- 附上错误日志和截图
- 说明运行环境（OS、Python 版本、HubStudio 版本）

### 提交 Pull Request

- Fork 项目并创建新分支
- 遵循现有代码风格
- 添加必要的测试
- 更新相关文档
- 提交前运行测试确保通过

---

## 致谢

- [HubStudio](https://www.hubstudio.cn/) - 提供指纹浏览器和 API
- [Ahrefs](https://ahrefs.com/) - 提供 SEO 数据
- [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/) - 提供浏览器自动化能力

---

**注意**: 本项目仅供学习和研究使用，请遵守相关服务条款。
