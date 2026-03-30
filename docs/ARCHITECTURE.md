# 技术架构文档

本文档详细说明 Ahrefs DR 批量查询工具的技术架构、数据流、API 协议、模块接口和扩展方法。

---

## 系统架构概览

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
│  • export_cookies()    │──▶│  • cookie_header (认证)         │
│  • get_env_list()      │   │  • proxy_url (SOCKS5代理)       │
│  • get_proxy_for_env() │──▶│  • get_domain_rating()         │
│  • build_cookie_header()│  │  • batch_get_domain_rating()   │
│  • build_proxy_url()   │   │  • get_overview_data()         │
└────────────────────────┘   └────────────────────────────────┘
             │                            │
             ▼                            ▼
┌────────────────────────┐   ┌────────────────────────────────┐
│  HubStudio Local API   │   │  Ahrefs Web API                │
│  http://127.0.0.1:6873 │   │  https://app.ahrefs.com        │
│  (本地指纹浏览器服务)     │   │  (通过 SOCKS5 代理访问)         │
└────────────────────────┘   └────────────────────────────────┘
```

---

## 配置模块：config.py

集中管理所有可配置参数，其他模块通过 `from config import ...` 引用。

### 配置项一览

| 变量名 | 类型 | 说明 | 必填 |
|--------|------|------|------|
| `HUBSTUDIO_API_BASE` | `str` | HubStudio 本地 API 地址 | ✅ |
| `APP_ID` | `str` | HubStudio APP ID 认证凭证 | ✅ |
| `APP_SECRET` | `str` | HubStudio APP Secret 认证凭证 | ✅ |
| `CONTAINER_CODE` | `str` | 已登录 Ahrefs 的浏览器环境 ID | ✅ |
| `SOCKS5_PROXY` | `str` | 手动指定代理 URL（留空则自动获取） | ❌ |
| `AHREFS_BASE_URL` | `str` | Ahrefs 网站基地址 | ✅ |
| `DEFAULT_HEADERS` | `dict` | 模拟浏览器的 HTTP 请求头 | ✅ |
| `DEFAULT_COUNTRY` | `str` | 默认国家代码 | ✅ |
| `REQUEST_DELAY` | `int` | 批量查询请求间隔（秒） | ✅ |
| `REQUEST_TIMEOUT` | `int` | 单次请求超时（秒） | ✅ |
| `MAX_RETRIES` | `int` | 失败重试次数 | ✅ |

---

## HubStudio 客户端：hubstudio.py

### 类：HubStudioClient

封装 HubStudio 指纹浏览器的本地 REST API。

#### 构造函数

```python
HubStudioClient(
    api_base: str = None,        # API 地址，默认从 config 读取
    container_code: str = None,  # 环境 ID，默认从 config 读取
    app_id: str = None,          # APP ID，默认从 config 读取
    app_secret: str = None       # APP Secret，默认从 config 读取
)
```

#### API 认证方式

所有请求通过 HTTP Header 传递凭证：

```
Content-Type: application/json
appId: <APP_ID>
appSecret: <APP_SECRET>
```

#### 方法列表

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `export_cookies(container_code?)` | `str` | `list[dict]` | 导出环境的全部 Cookie |
| `build_cookie_header(cookies, domain_filter?)` | `list, str` | `str` | 将 Cookie 列表转为 HTTP Header 字符串，可按域名过滤 |
| `get_env_list(container_codes?, page?, size?)` | `list, int, int` | `dict` | 获取环境列表（含代理信息） |
| `get_proxy_for_env(container_code?)` | `str` | `dict \| None` | 提取环境的代理配置 |
| `build_proxy_url(proxy_info)` | `dict` | `str` | 将代理配置转为 `socks5://host:port` 格式 URL |

#### HubStudio API 端点

| 端点 | 方法 | 请求体 | 响应 |
|------|------|--------|------|
| `/api/v1/env/export-cookie` | POST | `{"containerCode": "ID"}` | `{"code":0, "data": "[{cookie_json}]"}` |
| `/api/v1/env/list` | POST | `{"current":1, "size":50, "containerCodes":["ID"]}` | `{"code":0, "data":{"list":[...], "total":N}}` |
| `/api/v1/env/proxy/update` | POST | `{"containerCode":0, "proxyTypeName":"Socks5", ...}` | `{"code":0, "data":true}` |

#### Cookie 数据结构

`export_cookies()` 返回的每条 Cookie 格式：

```json
{
    "Name": "BSSESSID",
    "Value": "MUCw4tqh...",
    "Domain": ".ahrefs.com",
    "Path": "/",
    "Secure": true,
    "HttpOnly": false,
    "Persistent": "1",
    "Expires": "2024-09-13T15:18:07.389+08:00",
    "HasExpires": "1"
}
```

#### 环境列表数据结构

`get_env_list()` 返回的每个环境包含代理信息：

```json
{
    "containerCode": 8256337,
    "containerName": "环境名称",
    "proxyHost": "8.208.80.219",
    "proxyPort": 32080,
    "proxyTypeName": "Socks5",
    "proxyAccount": "",
    "proxyPassword": "",
    "lastUsedIp": "8.208.80.219"
}
```

---

## Ahrefs 客户端：ahrefs.py

### 类：AhrefsClient

通过已登录的 Cookie 和 SOCKS5 代理查询 Ahrefs 内部 API。

#### 构造函数

```python
AhrefsClient(
    cookie_header: str,      # Cookie 字符串 "name1=val1; name2=val2"
    proxy_url: str = None    # 代理 URL "socks5://host:port"
)
```

构造时创建 `requests.Session`，设置：
- `session.headers` ← `DEFAULT_HEADERS` + `cookie`
- `session.proxies` ← SOCKS5 代理（如有）

#### 方法列表

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `get_domain_rating(domain, country?)` | `str, str` | `dict` | 查询单个域名的 DR |
| `batch_get_domain_rating(domains, country?, delay?)` | `list, str, float` | `list[dict]` | 批量查询多个域名的 DR |
| `get_overview_data(domain, country?)` | `str, str` | `dict` | 获取域名的完整 Site Explorer 概览数据 |

#### Ahrefs API 端点

| 端点 | 方法 | 数据来源 |
|------|------|----------|
| `/v4/seGetDomainRating` | GET | Domain Rating + Ahrefs Rank |
| `/v4/seGetUrlRating` | GET | URL Rating |
| `/v4/seOverviewBacklinksStatsAll` | GET | 反链统计数据 |
| `/v4/seGetPagesByTrafficTopInput` | GET | 按流量排序的页面 |

#### 请求构造

所有 Ahrefs API 使用 GET 请求，参数通过 `?input=` 传递 JSON 字符串：

```
GET /v4/seGetDomainRating?input={"args":{"mode":"subdomains","protocol":"https","url":"example.com/","multiTarget":["Single",{"target":"example.com/","mode":"subdomains","protocol":"https"}],"compareDate":["Ago",["Month"]],"country":"us","backlinksFilter":null,"best_links_filter":"showAll","competitors":[]}}
```

#### 返回数据结构

`get_domain_rating()` 返回：

```json
{
    "domain": "example.com",
    "domain_rating": 86.0,
    "dr_delta": 0,
    "ahrefs_rank": 3756,
    "ar_delta": 27,
    "raw_response": { },
    "error": null
}
```

Ahrefs 原始 API 响应结构：

```json
{
    "result": {
        "data": {
            "ahrefsRank": {
                "value": 3756,
                "delta": 27
            },
            "domainRating": {
                "value": 86.0,
                "delta": 0
            }
        }
    }
}
```

#### 错误处理

| HTTP 状态码 | 处理方式 |
|-------------|----------|
| 200 | 正常解析 JSON 响应 |
| 403 | Cookie 过期或 IP 被封，立即返回错误 |
| 429 | 限流，等待 `delay * attempt * 3` 秒后重试 |
| 其他 | 重试最多 `MAX_RETRIES` 次 |
| 代理错误 | 重试最多 `MAX_RETRIES` 次 |

---

## CLI 入口：main.py

### 执行流程

```
1. parse_args()        解析命令行参数
       │
2. load_domains()      从 --domains 或 --file 加载域名列表
       │
3. setup_clients()     初始化客户端
       │
       ├── HubStudioClient.export_cookies()       导出 Cookie
       ├── HubStudioClient.build_cookie_header()   构建 Cookie 头（过滤 ahrefs.com）
       ├── HubStudioClient.get_proxy_for_env()     获取环境代理配置
       └── AhrefsClient(cookie, proxy)             创建 Ahrefs 客户端
       │
4. 执行查询
       │
       ├── --overview 模式: get_overview_data() 逐个查询完整概览
       └── 默认模式:      batch_get_domain_rating() 批量查询 DR
       │
5. 输出结果
       │
       ├── 默认: print_results_table() 表格输出
       ├── --json: JSON 格式输出到 stdout
       └── --output: export_csv() 导出 CSV 文件
```

### 代理优先级（从高到低）

1. CLI `--proxy` 参数手动指定
2. `config.py` 中的 `SOCKS5_PROXY` 值
3. HubStudio 环境自动获取的代理配置
4. 无代理（直接连接）

---

## 扩展开发指南

### 添加新的 Ahrefs 查询接口

1. 在 `ahrefs.py` 的 `AhrefsClient` 类中添加新方法
2. 构造 `input` JSON 参数（参考浏览器 DevTools Network 面板抓取的请求）
3. 使用 `self.session.get(url, params={"input": input_str})` 发送请求

示例 — 添加反链查询：

```python
def get_backlinks_stats(self, domain, country=None):
    input_str = self._build_dr_input(domain, country)  # 复用现有参数结构
    url = f"{self.base_url}/v4/seOverviewBacklinksStatsAll"
    resp = self.session.get(url, params={"input": input_str}, timeout=REQUEST_TIMEOUT)
    return resp.json()
```

### 添加新的 HubStudio 操作

在 `hubstudio.py` 的 `HubStudioClient` 类中添加新方法，调用 `self._post(path, payload)`。

可用 API 端点参考：https://api-docs.hubstudio.cn/

### 更换请求头

如果 Ahrefs 检测到请求异常，可在 `config.py` 的 `DEFAULT_HEADERS` 中更新 User-Agent 和 sec-ch-ua 等字段，使其与 HubStudio 环境的浏览器指纹一致。
