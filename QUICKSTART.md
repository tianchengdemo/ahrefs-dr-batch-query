# 快速入门指南

## 5 分钟快速上手

### 第一步：安装依赖

```bash
# 进入项目目录
cd D:\DEV\ahrefs

# 激活虚拟环境
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 第二步：配置 HubStudio

1. 打开 HubStudio 客户端
2. 点击 **设置** → **Local API**
3. 复制以下信息：
   - API 接口地址（通常是 `http://127.0.0.1:6873`）
   - APP ID
   - APP Secret

4. 在 HubStudio 中找到已登录 Ahrefs 的环境
5. 复制环境 ID（containerCode）

### 第三步：填写配置

编辑 `config.py`：

```python
HUBSTUDIO_API_BASE = "http://127.0.0.1:6873"
APP_ID = "202304081094355194931703808"        # 替换为你的 APP ID
APP_SECRET = "202304081094355194931703808"    # 替换为你的 APP Secret
CONTAINER_CODE = "970506927"                  # 替换为你的环境 ID
```

### 第四步：运行查询

```bash
python main.py --domains "example.com"
```

**预期输出：**

```
[域名] 已加载 1 个域名
[HubStudio] 正在重启浏览器以启用 CDP...
[HubStudio] 浏览器已关闭
[HubStudio] 浏览器已启动，调试端口: 58013
[HubStudio] 等待页面加载...
[HubStudio] 通过 CDP 获取 Cookie（包括 HttpOnly）...
[HubStudio] 成功获取 14 个 Cookie（含 11 个 HttpOnly）
[代理] 使用: socks5://user:pass@host:port
[Ahrefs] 使用代理: socks5://user:pass@host:port

============================================================
  开始批量查询 1 个域名的 Domain Rating
============================================================

--- [1/1] example.com ---
[Ahrefs] 查询 DR: example.com (尝试 1/3)
[Ahrefs] [OK] example.com → DR: 93.0, AR: 120

============================================================
  查询结果
============================================================

域名                                     DR       AR         状态
----------------------------------------------------------------------
  example.com                            93.0     120        [OK]

  总计: 1 个域名, 成功: 1, 失败: 0
============================================================
```

## 常用命令

### 查询单个域名
```bash
python main.py --domains "example.com"
```

### 批量查询多个域名
```bash
python main.py --domains "example.com,google.com,github.com"
```

### 从文件批量查询
创建 `domains.txt`：
```
example.com
google.com
github.com
```

运行：
```bash
python main.py --file domains.txt
```

### 导出为 CSV
```bash
python main.py --domains "example.com,google.com" --output results.csv
```

### JSON 格式输出
```bash
python main.py --domains "example.com" --json
```

## 工作流程说明

### 自动化流程

1. **启动阶段**
   - 程序自动关闭 HubStudio 浏览器（如果正在运行）
   - 重新启动浏览器，添加 CDP 参数
   - 自动打开 `https://app.ahrefs.com`

2. **Cookie 获取**
   - 等待页面加载完成（5秒）
   - 通过 CDP WebSocket 连接浏览器
   - 调用 `Network.getCookies` 获取所有 Cookie
   - 包括 HttpOnly Cookie（如 BSSESSID）

3. **数据查询**
   - 使用获取的 Cookie 发送请求
   - 通过 SOCKS5 代理访问 Ahrefs API
   - 解析响应并输出结果

### 为什么需要重启浏览器？

HubStudio 默认启动的浏览器不允许外部 CDP 连接（安全限制）。程序需要添加 `--remote-allow-origins=*` 参数来允许 CDP 连接，因此需要重启浏览器。

### 为什么需要 CDP？

Ahrefs 的会话认证依赖 `BSSESSID` Cookie，这是一个 **HttpOnly** Cookie。出于安全考虑，HubStudio API 无法导出 HttpOnly Cookie，只能通过 CDP 协议直接从浏览器获取。

## 故障排查

### 问题 1: 连接 HubStudio 失败

**错误信息：**
```
[HubStudio] 获取失败: HubStudio API Error: 请求参数路径是否正确
```

**解决方案：**
1. 确认 HubStudio 客户端已启动
2. 检查 Local API 状态是否为"正常"
3. 验证 `config.py` 中的 API 地址、APP_ID、APP_SECRET 是否正确

### 问题 2: 浏览器启动失败

**错误信息：**
```
[HubStudio] 获取失败: HubStudio API Error: 环境不存在
```

**解决方案：**
1. 在 HubStudio 中确认环境 ID 是否正确
2. 确认该环境属于当前登录的账号
3. 检查环境是否已被删除

### 问题 3: CDP 连接失败

**错误信息：**
```
[CDP] 获取 Cookie 失败: Handshake status 403 Forbidden
```

**解决方案：**
- 程序会自动回退到 API 方式
- 如果 API 方式也失败（401 错误），说明需要重新登录 Ahrefs
- 在 HubStudio 浏览器中访问 app.ahrefs.com 并登录

### 问题 4: 401 Unauthorized

**错误信息：**
```
[Ahrefs] [ERROR] 请求失败: 401 Client Error: Unauthorized
```

**解决方案：**
1. 确认 HubStudio 环境中已登录 Ahrefs
2. 检查日志，确认是否成功获取 HttpOnly Cookie
3. 如果 CDP 获取失败，手动在浏览器中重新登录 Ahrefs

### 问题 5: 代理连接失败

**错误信息：**
```
[Ahrefs] [ERROR] 代理连接失败
```

**解决方案：**
1. 检查 HubStudio 环境的代理配置
2. 测试代理是否可用
3. 使用 `--proxy` 参数手动指定代理：
   ```bash
   python main.py --domains "example.com" --proxy "socks5://host:port"
   ```

## 高级用法

### 指定国家代码

查询特定国家的数据：

```bash
python main.py --domains "example.com" --country br  # 巴西
python main.py --domains "example.com" --country jp  # 日本
python main.py --domains "example.com" --country de  # 德国
```

### 调整请求间隔

避免触发限流：

```bash
python main.py --domains "example.com,google.com" --delay 5
```

### 获取完整概览数据

除了 DR 和 AR，还包括 UR、反链数、流量等：

```bash
python main.py --domains "example.com" --overview
```

### 手动指定代理

覆盖 HubStudio 环境的代理配置：

```bash
python main.py --domains "example.com" --proxy "socks5://user:pass@host:port"
```

## 性能优化建议

### 1. 批量查询优化

- 每次查询间隔 2 秒（默认），避免触发限流
- 建议每批不超过 50 个域名
- 大量查询时分批执行

### 2. 代理选择

- 使用稳定的住宅代理
- 避免使用数据中心 IP（容易被封）
- 定期更换代理 IP

### 3. Cookie 管理

- CDP 方式获取的 Cookie 包含完整会话信息
- 浏览器重启后 Cookie 会更新
- 无需手动管理 Cookie 过期

## 下一步

- 查看 [README.md](README.md) 了解完整功能
- 查看 [ARCHITECTURE.md](ARCHITECTURE.md) 了解技术架构
- 参考 [HubStudio API 文档](https://api-docs.hubstudio.cn/) 了解更多 API 用法

## 获取帮助

如遇到问题：

1. 查看本文档的"故障排查"部分
2. 检查程序输出的日志信息
3. 确认 HubStudio 和 Ahrefs 账号状态
4. 提交 Issue 到项目仓库

---

**提示**: 首次运行时浏览器会重启，这是正常现象。后续运行会更快。
