# Docker 部署

## 当前 Docker 结构

当前 Compose 包含三个服务：

- `ahrefs-api`：FastAPI 服务
- `ahrefs-redis`：热点缓存
- `ahrefs-caddy`：域名反代和自动 HTTPS

推荐模式：

- API 跑在 Docker 中
- HubStudio 跑在宿主机
- API 容器通过 `host.docker.internal` 访问 HubStudio
- Redis 只做热点缓存
- SQLite 作为持久化缓存
- Caddy 负责域名和证书

## 必要配置

### `config.py`

如果 Docker 内要访问宿主机 HubStudio：

```python
HUBSTUDIO_API_BASE = "http://host.docker.internal:6873"
HUBSTUDIO_CDP_HOST = "host.docker.internal"
```

如果不走 HubStudio，也可以只依赖：

```python
AHREFS_COOKIE = "..."
```

### `.env`

复制 `.env.example` 为 `.env`，填写：

```dotenv
CADDY_DOMAIN=dr.lookav.net
```

## 启动

```powershell
docker compose up -d --build
```

停止：

```powershell
docker compose down
```

查看状态：

```powershell
docker compose ps
```

在容器内运行测试：

```powershell
docker compose run --rm api python -m unittest discover -s tests -v
```

## 域名访问

Compose 暴露：

- `80/tcp`
- `443/tcp`
- `127.0.0.1:8000` 仅供本机调试

Caddy 会把：

```text
https://$CADDY_DOMAIN
```

反代到：

```text
api:8000
```

例如：

```text
https://dr.lookav.net/health
https://dr.lookav.net/docs
https://dr.lookav.net/api/query
```

## Windows 服务器注意事项

如果部署在 Windows 公网服务器：

- 确保 Docker Desktop 正常运行
- 确保 Windows 防火墙放行 `80` 和 `443`
- 如果用了 Cloudflare，首次申请证书时要保证源站可回源
- Caddy 成功签证后即可直接通过域名访问 API

## 挂载

Compose 当前挂载：

- `./config.py:/app/config.py:ro`
- `./.omc:/app/.omc`
- `./cookies.txt:/app/cookies.txt:ro`
- `caddy_data:/data`
- `caddy_config:/config`

作用：

- 私有配置不进镜像
- SQLite 跨容器重启持久化
- Cookie 文件可作为兜底
- Caddy 证书会持久化保存

## Redis 热点缓存

当前缓存策略：

- Redis 只缓存热点 key
- SQLite 仍是持久化数据源
- SQLite 命中后会重新回填 Redis

当前限制：

- Redis 持久化关闭
- 最大内存 `2048mb`
- 淘汰策略 `allkeys-lru`

Compose 中对应参数：

```text
--maxmemory 2048mb
--maxmemory-policy allkeys-lru
```

## 限制

当前 Docker 只容器化了 API 相关服务。

没有容器化的部分：

- HubStudio 本体
- 指纹浏览器

它们仍然运行在宿主机。
