# Ahrefs DR 批量查询工具

通过 HubStudio 指纹浏览器自动获取已登录 Ahrefs 账号的 Cookie（包括 HttpOnly），结合 SOCKS5 代理，批量查询域名的 Domain Rating (DR) 及其他 SEO 指标。

## 核心特性

- ✅ **完全自动化** - 自动通过 CDP 协议获取所有 Cookie（包括 HttpOnly）
- ✅ **零手动操作** - 无需手动复制 Cookie 或配置会话信息
- ✅ **HubStudio 集成** - 自动管理浏览器启动、Cookie 获取、代理配置
- ✅ **批量查询** - 支持查询多个域名的 DR 和 Ahrefs Rank
- ✅ **多种输出格式** - 支持表格、JSON、CSV 导出

## 项目结构

```
ahrefs/
├── config.py           # 全局配置（HubStudio API、代理、请求头）
├── hubstudio.py        # HubStudio 指纹浏览器 API 客户端
├── ahrefs.py           # Ahrefs 数据查询客户端
├── main.py             # CLI 命令行入口
├── requirements.txt    # Python 依赖
├── README.md           # 本文件
├── ARCHITECTURE.md     # 技术架构文档
└── .venv/              # Python 虚拟环境
```

## 前置条件

1. **HubStudio 指纹浏览器** 已安装并运行，且 Local API 处于"正常"状态
2. 至少一个 HubStudio 环境已 **登录 Ahrefs 账号**
3. 该环境已配置 **SOCKS5 代理**（工具会自动读取环境代理配置）
4. Python 3.10+

## 快速开始

### 1. 安装依赖

```bash
cd D:\DEV\ahrefs
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置

编辑 `config.py`，填入以下信息（从 HubStudio 客户端 → 设置 → Local API 页面获取）：

```python
HUBSTUDIO_API_BASE = "http://127.0.0.1:6873"   # API 接口地址
APP_ID = "你的APP_ID"                            # APP ID
APP_SECRET = "你的APP_SECRET"                    # APP Secret
CONTAINER_CODE = "你的环境ID"                     # 已登录Ahrefs的环境ID
```

### 3. 使用

```bash
# 查询单个域名
python main.py --domains "example.com"

# 查询多个域名（逗号分隔）
python main.py --domains "example.com,google.com,github.com"

# 从文件批量查询（每行一个域名）
python main.py --file domains.txt

# 指定国家代码
python main.py --domains "example.com" --country br

# 导出 CSV
python main.py --domains "example.com,google.com" --output results.csv

# JSON 格式输出
python main.py --domains "example.com" --json

# 获取完整概览数据（DR + UR + 反链 + 流量等）
python main.py --domains "example.com" --overview

# 手动指定代理（覆盖 HubStudio 环境代理）
python main.py --domains "example.com" --proxy "socks5://127.0.0.1:1080"
```

## 工作原理

### 自动化 Cookie 获取流程

1. **关闭浏览器** - 自动关闭 HubStudio 环境（如果正在运行）
2. **启动浏览器** - 使用 CDP 参数 `--remote-allow-origins=*` 重新启动
3. **打开页面** - 自动访问 `https://app.ahrefs.com` 并等待加载
4. **CDP 连接** - 通过 Chrome DevTools Protocol 连接浏览器
5. **获取 Cookie** - 调用 `Network.getCookies` 获取所有 Cookie（包括 HttpOnly）
6. **查询数据** - 使用获取的 Cookie 查询域名 DR 数据

### Cookie 获取策略

```
┌─────────────────────────────────────────────────────────┐
│  优先级 1: CDP 协议获取（推荐）                           │
│  - 包含所有 Cookie（含 HttpOnly 如 BSSESSID）            │
│  - 自动启动浏览器并打开 ahrefs.com                       │
│  - 等待页面加载后通过 WebSocket 获取                     │
└─────────────────────────────────────────────────────────┘
                        ↓ 失败
┌─────────────────────────────────────────────────────────┐
│  优先级 2: HubStudio API 导出                            │
│  - 只能获取非 HttpOnly Cookie                            │
│  - 缺少关键会话 Cookie（BSSESSID）                       │
│  - 会导致 401 认证失败                                   │
└─────────────────────────────────────────────────────────┘
                        ↓ 失败
┌─────────────────────────────────────────────────────────┐
│  优先级 3: 手动配置（回退方案）                          │
│  - 从 cookies.txt 读取手动配置的 Cookie                  │
│  - 需要用户手动从浏览器复制                              │
└─────────────────────────────────────────────────────────┘
```

## CLI 参数说明

| 参数 | 短名 | 说明 | 默认值 |
|------|------|------|--------|
| `--domains` | `-d` | 域名列表，逗号分隔 | — |
| `--file` | `-f` | 域名文件路径 | — |
| `--country` | `-c` | 国家代码 | `us` |
| `--output` | `-o` | CSV 输出文件路径 | — |
| `--overview` | — | 获取完整概览数据 | `false` |
| `--proxy` | `-p` | 手动指定代理 URL | 自动读取 |
| `--delay` | — | 请求间隔秒数 | `2` |
| `--json` | — | JSON 格式输出 | `false` |

## 输出示例

### 表格输出（默认）
```
============================================================
  查询结果
============================================================

域名                                     DR       AR         状态
----------------------------------------------------------------------
  example.com                            93.0     120        [OK]
  google.com                             99.0     3          [OK]
  github.com                             96.0     19         [OK]

  总计: 3 个域名, 成功: 3, 失败: 0
============================================================
```

### JSON 输出（`--json`）
```json
[
  {
    "domain": "example.com",
    "domain_rating": 93.0,
    "dr_delta": 0.0,
    "ahrefs_rank": 120,
    "ar_delta": -3
  },
  {
    "domain": "google.com",
    "domain_rating": 99.0,
    "dr_delta": 0.0,
    "ahrefs_rank": 3,
    "ar_delta": 0
  }
]
```

## 技术架构

### 系统架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                        main.py (CLI)                        │
│  解析命令行参数 → 协调 HubStudio 和 Ahrefs 客户端 → 输出结果  │
└────────────┬────────────────────────────┬───────────────────┘
             │                            │
             ▼                            ▼
┌────────────────────────┐   ┌────────────────────────────────┐
│   hubstudio.py         │   │   ahrefs.py                    │
│   HubStudioClient      │   │   AhrefsClient                 │
│                        │   │                                │
│  • start_browser()     │──▶│  • cookie_header (认证)         │
│  • stop_browser()      │   │  • proxy_url (SOCKS5代理)       │
│  • get_cookies_via_cdp()│─▶│  • get_domain_rating()         │
│  • export_cookies()    │   │  • batch_get_domain_rating()   │
│  • get_proxy_for_env() │──▶│  • get_overview_data()         │
└────────────────────────┘   └────────────────────────────────┘
             │                            │
             ▼                            ▼
┌────────────────────────┐   ┌────────────────────────────────┐
│  HubStudio Local API   │   │  Ahrefs Web API                │
│  http://127.0.0.1:6873 │   │  https://app.ahrefs.com        │
│  (本地指纹浏览器服务)     │   │  (通过 SOCKS5 代理访问)         │
└────────────────────────┘   └────────────────────────────────┘
             │
             ▼
┌────────────────────────┐
│  Chrome DevTools       │
│  Protocol (CDP)        │
│  WebSocket 连接         │
└────────────────────────┘
```

### CDP Cookie 获取流程

```
1. 启动浏览器
   POST /api/v1/browser/start
   {
     "containerCode": 970506927,
     "args": ["--remote-allow-origins=*"],
     "containerTabs": ["https://app.ahrefs.com"]
   }
   ↓
   返回 debuggingPort: 58013

2. 获取页面列表
   GET http://127.0.0.1:58013/json
   ↓
   返回 webSocketDebuggerUrl

3. 建立 WebSocket 连接
   ws://127.0.0.1:58013/devtools/page/xxx
   ↓
   发送命令: {"id": 1, "method": "Network.getCookies"}
   ↓
   接收响应: {"result": {"cookies": [...]}}

4. 过滤 ahrefs.com Cookie
   包括 HttpOnly Cookie (BSSESSID)
```

## 常见问题

### 1) CDP 连接失败 (403 Forbidden)

**原因**: 浏览器未启用 `--remote-allow-origins=*` 参数

**解决**: 程序会自动重启浏览器并添加该参数，无需手动操作

### 2) 401 Unauthorized

**原因**: Cookie 缺少会话认证信息（BSSESSID）

**解决**:
- 确保使用 CDP 方式获取 Cookie（程序默认）
- 检查 HubStudio 环境是否已登录 Ahrefs
- 查看日志确认是否成功获取 HttpOnly Cookie

### 3) 浏览器启动失败

**原因**:
- HubStudio 客户端未运行
- API 凭证配置错误
- 环境 ID 不存在

**解决**:
- 确认 HubStudio 已启动，Local API 显示"正常"
- 检查 `config.py` 中的 `APP_ID`、`APP_SECRET`、`CONTAINER_CODE`
- 在 HubStudio 中确认环境存在且属于当前账号

### 4) 代理连接失败

**原因**: HubStudio 环境的代理配置不可用

**解决**:
- 检查 HubStudio 环境的代理配置是否正确
- 测试代理是否可用
- 使用 `--proxy` 参数手动指定代理

### 5) 查询返回 DR: None

**原因**: API 响应格式变化或解析失败

**解决**:
- 检查 Ahrefs API 是否正常
- 查看日志中的响应内容
- 确认域名格式正确

## 依赖说明

```txt
requests          # HTTP 请求库
pysocks           # SOCKS5 代理支持
websocket-client  # WebSocket 客户端（CDP 连接）
```

## 更新日志

### v2.0.0 (2026-03-29)

**重大更新：完全自动化 Cookie 获取**

- ✅ 新增 CDP 协议支持，自动获取所有 Cookie（包括 HttpOnly）
- ✅ 自动管理浏览器启动/关闭，无需手动操作
- ✅ 自动打开 ahrefs.com 页面并等待加载
- ✅ 智能回退机制：CDP → API → 手动配置
- ✅ 修复 Windows 控制台中文编码问题
- ✅ 修复 Ahrefs API 响应解析（支持数组格式）
- ✅ 优化代理配置自动获取
- ✅ 移除手动配置 BSSESSID 的需求

### v1.0.0 (2026-03-21)

**初始版本**

- ✅ HubStudio API 集成
- ✅ 批量查询域名 DR
- ✅ 支持 SOCKS5 代理
- ✅ 多种输出格式（表格、JSON、CSV）

## 参考文档

- HubStudio API 文档: https://api-docs.hubstudio.cn/
- HubStudio Skill 示例: https://github.com/hubstudio-Max/hubstudio-skill
- Chrome DevTools Protocol: https://chromedevtools.github.io/devtools-protocol/
- Ahrefs 官网: https://ahrefs.com/

## 许可证

本项目仅供学习和研究使用。

## 贡献

欢迎提交 Issue 和 Pull Request！

---

**注意**: 请遵守 Ahrefs 的服务条款，合理使用 API，避免频繁请求导致账号被封。
