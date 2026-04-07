# Configuration

All configuration is via environment variables. ragdeck does not use a config file.

## Required

| Variable | Description |
|----------|-------------|
| `RAGDECK_ADMIN_TOKEN` | Bearer token for all ragdeck admin API calls. Set to a long random string. |

## Service URLs

| Variable | Default | Description |
|----------|---------|-------------|
| `RAGPIPE_URL` | `http://host.containers.internal:8090` | ragpipe API URL |
| `RAGSTUFFER_URL` | `http://host.containers.internal:8091` | ragstuffer API URL |
| `RAGSTUFFER_MPEP_URL` | `http://host.containers.internal:8093` | ragstuffer-mpep API URL (MPEP-only ingest service) |
| `RAGWATCH_URL` | `http://host.containers.internal:9090` | ragwatch Prometheus aggregator URL |
| `RAGORCHESTRATOR_URL` | `http://host.containers.internal:8095` | ragorchestrator LangGraph agent URL |
| `QDRANT_URL` | `http://host.containers.internal:6333` | Qdrant vector database URL |
| `DOCSTORE_URL` | *(required)* | Postgres connection string, e.g. `postgresql://user:pass@localhost:5432/ragdeck` |

## Service Tokens

| Variable | Description |
|----------|-------------|
| `RAGPIPE_ADMIN_TOKEN` | Token for ragpipe admin endpoints (reload-routes, reload-prompt, admin/config). Passed through in admin UI actions. |
| `RAGSTUFFER_ADMIN_TOKEN` | Token for ragstuffer admin endpoints (ingest trigger). Passed through in ingest UI actions. |

## Container Runtime

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8092` | TCP port ragdeck listens on |

## Hardware-Specific

| Variable | Default | Description |
|----------|---------|-------------|
| `QDRANT__SERVICE__HOST` | `::` | Set to `::` (IPv6 all-interfaces) or `0.0.0.0` for IPv4. Qdrant requires this for IPv4 on some setups. |

## Example: Podman quadlet

```bash
podman run --rm -p 8092:8092 \
  --env RAGDECK_ADMIN_TOKEN=your-secure-token \
  --env DOCSTORE_URL=postgresql://postgres@host.containers.internal:5432/ragdeck \
  --env RAGPIPE_URL=http://host.containers.internal:8090 \
  --env RAGPIPE_ADMIN_TOKEN=ragpipe-token \
  --env RAGSTUFFER_URL=http://host.containers.internal:8091 \
  --env RAGSTUFFER_ADMIN_TOKEN=ragstuffer-token \
  --env RAGWATCH_URL=http://host.containers.internal:9090 \
  --env RAGORCHESTRATOR_URL=http://host.containers.internal:8095 \
  --env QDRANT_URL=http://host.containers.internal:6333 \
  ghcr.io/aclater/ragdeck:main
```

## Example: docker-compose fragment

```yaml
ragdeck:
  image: ghcr.io/aclater/ragdeck:main
  ports:
    - "8092:8092"
  env_file: ragstack.env
  environment:
    RAGDECK_ADMIN_TOKEN: "${RAGDECK_ADMIN_TOKEN}"
    DOCSTORE_URL: "postgresql://postgres@host.containers.internal:5432/ragdeck"
    RAGPIPE_URL: "http://ragpipe:8090"
    RAGSTUFFER_URL: "http://ragstuffer:8091"
    RAGWATCH_URL: "http://ragwatch:9090"
    RAGORCHESTRATOR_URL: "http://ragorchestrator:8095"
    QDRANT_URL: "http://qdrant:6333"
```
