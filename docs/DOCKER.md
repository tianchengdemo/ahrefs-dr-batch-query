# Docker Deployment

## What Works

The Docker stack now includes:

- `ahrefs-api` for the FastAPI service
- `ahrefs-redis` for hot-cache storage
- `ahrefs-caddy` for domain binding and automatic HTTPS

Best-supported mode:

- API runs in Docker
- Caddy terminates HTTPS and reverse-proxies to the API container
- HubStudio runs on the host machine
- the API container connects to HubStudio through `host.docker.internal`
- Redis stores hot keys only
- SQLite remains the persistent local database

## Required Config

In `config.py`:

```python
HUBSTUDIO_API_BASE = "http://host.docker.internal:6873"
HUBSTUDIO_CDP_HOST = "host.docker.internal"
```

If you do not want HubStudio integration in Docker, you can instead rely on:

```python
AHREFS_COOKIE = "..."
```

Copy `.env.example` to `.env`, then set your real domain:

```dotenv
CADDY_DOMAIN=api.example.com
```

`CADDY_DOMAIN` must already resolve to your server public IP.

## Start

```powershell
docker compose up -d --build
```

Stop:

```powershell
docker compose down
```

## Domain Binding

Compose exposes:

- `80/tcp` for HTTP challenge and redirect
- `443/tcp` for HTTPS
- `127.0.0.1:8000` for local host debugging only

Caddy reads `deploy/Caddyfile` and reverse-proxies:

- `https://$CADDY_DOMAIN` -> `api:8000`

Examples:

```text
https://api.example.com/health
https://api.example.com/api/query
```

If you use an external firewall or cloud security group, allow inbound:

- `80`
- `443`

## Files

- `Dockerfile.api`
- `docker-compose.yml`
- `deploy/Caddyfile`
- `.dockerignore`

## Volumes

Compose mounts:

- `./config.py:/app/config.py:ro`
- `./.omc:/app/.omc`
- `./cookies.txt:/app/cookies.txt:ro`
- `caddy_data:/data`
- `caddy_config:/config`

This keeps:

- private config outside the image
- SQLite cache persistent across container restarts
- cookie fallback available when needed
- Caddy certificates persistent across container restarts

## Redis Hot Cache

Compose also starts a Redis container:

- `ahrefs-redis`

Cache strategy:

- Redis stores hot keys only
- SQLite remains the durable local store
- SQLite hits can repopulate Redis

Capacity control:

- Redis persistence is disabled
- memory limit is `2048mb`
- eviction policy is `allkeys-lru`

Compose sets:

```text
--maxmemory 2048mb
--maxmemory-policy allkeys-lru
```

## Limitations

The current Docker setup is for the API service.

It does not containerize:

- HubStudio itself
- the fingerprint browser

Those still run on the host.
