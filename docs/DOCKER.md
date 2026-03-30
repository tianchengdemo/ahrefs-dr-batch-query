# Docker Deployment

## What Works

The API can run in Docker.

Best-supported mode:

- API runs in a container
- HubStudio runs on the host machine
- the container connects to HubStudio through `host.docker.internal`
- Redis runs in a separate container as a hot cache
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

## Start

```powershell
docker compose up -d --build
```

Stop:

```powershell
docker compose down
```

## Files

- `Dockerfile.api`
- `docker-compose.yml`
- `.dockerignore`

## Volumes

Compose mounts:

- `./config.py:/app/config.py:ro`
- `./.omc:/app/.omc`
- `./cookies.txt:/app/cookies.txt:ro`

This keeps:

- private config outside the image
- SQLite cache persistent across container restarts
- cookie fallback available when needed

## Redis Hot Cache

Compose also starts a Redis container:

- `ahrefs-redis`

Cache strategy:

- Redis stores hot keys only
- SQLite remains the durable local store
- SQLite hits can repopulate Redis

Capacity control:

- Redis persistence is disabled
- memory limit is `128mb`
- eviction policy is `allkeys-lru`

Compose sets:

```text
--maxmemory 128mb
--maxmemory-policy allkeys-lru
```

## Limitations

The current Docker setup is for the API service.

It does not containerize:

- HubStudio itself
- the fingerprint browser

Those still run on the host.
