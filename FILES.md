# 项目文件说明

## 核心文件

### 主程序文件

| 文件 | 大小 | 说明 |
|------|------|------|
| `main.py` | 9.2K | CLI 命令行入口，参数解析，流程协调 |
| `ahrefs.py` | 11K | Ahrefs API 客户端，数据查询，响应解析 |
| `hubstudio.py` | 5.4K | HubStudio API 客户端，浏览器管理，CDP 连接 |
| `config.py` | 2.9K | 全局配置文件（包含用户凭证） |
| `config.example.py` | 4.1K | 配置文件示例（供参考） |

### 依赖文件

| 文件 | 大小 | 说明 |
|------|------|------|
| `requirements.txt` | 34B | Python 依赖包列表 |

## 文档文件

### 用户文档

| 文件 | 大小 | 说明 |
|------|------|------|
| `README.md` | 13K | 项目主文档，功能介绍，使用说明 |
| `QUICKSTART.md` | 6.8K | 快速入门指南，5 分钟上手 |
| `CHANGELOG.md` | 5.0K | 更新日志，版本历史 |

### 技术文档

| 文件 | 大小 | 说明 |
|------|------|------|
| `ARCHITECTURE.md` | 11K | 技术架构文档，系统设计 |
| `PROJECT_SUMMARY.md` | 6.5K | 项目总结，技术要点 |

## 测试/调试文件

| 文件 | 大小 | 说明 |
|------|------|------|
| `test_hubstudio.py` | 1.5K | HubStudio 连接测试 |
| `test_request.py` | 809B | 请求测试脚本 |
| `debug_cookie.py` | 570B | Cookie 调试脚本 |
| `debug_all_cookies.py` | 747B | 查看所有 Cookie |
| `start_browser.py` | 722B | 浏览器启动测试 |
| `manual_cookie_guide.py` | 809B | 手动 Cookie 获取指南 |

## 目录结构

```
ahrefs/
├── .venv/                      # Python 虚拟环境
│   ├── Lib/                    # 依赖库
│   ├── Scripts/                # 可执行文件
│   └── pyvenv.cfg              # 虚拟环境配置
│
├── .claude/                    # Claude 配置目录
│   └── memory/                 # 会话记忆
│
├── __pycache__/                # Python 缓存
│
├── 核心程序文件
│   ├── main.py                 # CLI 入口
│   ├── ahrefs.py               # Ahrefs 客户端
│   ├── hubstudio.py            # HubStudio 客户端
│   ├── config.py               # 配置文件（用户填写）
│   └── config.example.py       # 配置示例
│
├── 文档文件
│   ├── README.md               # 主文档
│   ├── QUICKSTART.md           # 快速入门
│   ├── CHANGELOG.md            # 更新日志
│   ├── ARCHITECTURE.md         # 技术架构
│   └── PROJECT_SUMMARY.md      # 项目总结
│
├── 测试文件
│   ├── test_hubstudio.py       # HubStudio 测试
│   ├── test_request.py         # 请求测试
│   ├── debug_cookie.py         # Cookie 调试
│   ├── debug_all_cookies.py    # 查看所有 Cookie
│   ├── start_browser.py        # 浏览器启动测试
│   └── manual_cookie_guide.py  # 手动指南
│
└── 依赖文件
    └── requirements.txt        # Python 依赖
```

## 文件用途说明

### 必需文件（运行必须）

1. **main.py** - 程序入口，必须存在
2. **ahrefs.py** - 核心查询逻辑，必须存在
3. **hubstudio.py** - HubStudio 集成，必须存在
4. **config.py** - 配置文件，必须填写
5. **requirements.txt** - 依赖列表，安装时需要

### 可选文件（可删除）

1. **test_*.py** - 测试脚本，调试用
2. **debug_*.py** - 调试脚本，排查问题用
3. **start_browser.py** - 浏览器测试，开发用
4. **manual_cookie_guide.py** - 手动指南，已不需要
5. **config.example.py** - 配置示例，参考用

### 文档文件（建议保留）

1. **README.md** - 主文档，了解项目
2. **QUICKSTART.md** - 快速入门，新手必读
3. **CHANGELOG.md** - 更新日志，版本追踪
4. **ARCHITECTURE.md** - 技术架构，深入理解
5. **PROJECT_SUMMARY.md** - 项目总结，技术要点

## 配置文件说明

### config.py（必须配置）

```python
# 必填项
HUBSTUDIO_API_BASE = "http://127.0.0.1:6873"
APP_ID = "你的APP_ID"
APP_SECRET = "你的APP_SECRET"
CONTAINER_CODE = "你的环境ID"

# 可选项（留空则自动获取）
SOCKS5_PROXY = ""
AHREFS_COOKIE = ""
```

### 配置获取步骤

1. 打开 HubStudio → 设置 → Local API
2. 复制 API 地址、APP ID、APP Secret
3. 在环境列表中找到已登录 Ahrefs 的环境
4. 复制环境 ID（containerCode）
5. 填写到 config.py

## 依赖说明

### requirements.txt

```txt
requests          # HTTP 请求库
pysocks           # SOCKS5 代理支持
websocket-client  # WebSocket 客户端（CDP 连接）
```

### 安装命令

```bash
pip install -r requirements.txt
```

## 运行环境

### 系统要求

- **操作系统**: Windows 10/11, macOS, Linux
- **Python**: 3.10+
- **HubStudio**: 最新版本
- **网络**: 需要 SOCKS5 代理

### 磁盘空间

- 项目文件: ~100KB
- 虚拟环境: ~50MB
- 依赖库: ~10MB
- 总计: ~60MB

### 内存占用

- 运行时: ~50MB
- 浏览器: ~200MB
- 总计: ~250MB

## 清理建议

### 可以删除的文件

开发完成后，可以删除以下文件以减小项目体积：

```bash
# 删除测试文件
rm test_*.py debug_*.py start_browser.py manual_cookie_guide.py

# 删除配置示例
rm config.example.py

# 删除 Python 缓存
rm -rf __pycache__

# 保留核心文件
# main.py, ahrefs.py, hubstudio.py, config.py
# README.md, QUICKSTART.md, requirements.txt
```

### 最小化部署

最小化部署只需要以下文件：

```
ahrefs/
├── main.py
├── ahrefs.py
├── hubstudio.py
├── config.py
├── requirements.txt
└── README.md
```

总大小: ~40KB（不含虚拟环境）

## 备份建议

### 重要文件（必须备份）

1. **config.py** - 包含凭证信息
2. **自定义脚本** - 如果有修改

### 不需要备份

1. **虚拟环境** - 可重新创建
2. **缓存文件** - 可重新生成
3. **测试文件** - 可从源码恢复

## 版本控制

### .gitignore 建议

```gitignore
# 虚拟环境
.venv/
venv/

# Python 缓存
__pycache__/
*.pyc
*.pyo

# 配置文件（包含敏感信息）
config.py
cookies.txt

# 输出文件
*.csv
results/

# IDE 配置
.vscode/
.idea/

# 日志文件
*.log

# 临时文件
*.tmp
*.bak
```

### 提交建议

- ✅ 提交核心代码文件
- ✅ 提交文档文件
- ✅ 提交配置示例（config.example.py）
- ❌ 不提交配置文件（config.py）
- ❌ 不提交虚拟环境
- ❌ 不提交缓存文件

---

**最后更新**: 2026-03-30

**项目版本**: v2.0.0
