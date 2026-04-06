# ragdeck

Admin UI for the rag-suite stack. Single-pane management for all services — collections, ingest, query log, probe runs, metrics.

## What it does

ragdeck is the administrative control plane for the rag-suite. It provides a unified interface to:

- **Collections** — browse Qdrant collections across all routes, view collection stats
- **Ingest** — monitor ragstuffer job status, view processing queues
- **Query log** — search and filter the ragpipe query log, inspect grounding decisions and citations
- **Metrics** — real-time dashboards powered by ragwatch (Prometheus + Grafana)

## How it fits into rag-suite

```
┌─────────────────────────────────────────────┐
│                  ragdeck                     │
│  ┌──────────┬──────────┬──────────┬───────┐ │
│  │Collections│  Ingest  │Query Log │Metrics│ │
│  └────┬─────┴────┬─────┴────┬─────┴───┬───┘ │
└───────┼──────────┼──────────┼─────────┼─────┘
        │          │          │         │
   ┌────▼────┐ ┌───▼────┐ ┌──▼────┐ ┌──▼──────┐
   │ Qdrant  │ │ragstuff│ │ragpipe│ │ragwatch │
   │         │ │  er    │ │       │ │(Prometheus)│
   └─────────┘ └────────┘ └───────┘ └─────────┘
                                     │
                                ┌────▼────┐
                                │ Grafana │
                                └─────────┘
```

## Quick start (container)

```bash
# Pull the published image
podman pull ghcr.io/aclater/ragdeck:main

# Run with admin token
podman run --rm -p 8092:8092 \
    -e RAGDECK_ADMIN_TOKEN=your-secure-token \
    -e RAGPIPE_URL=http://localhost:8090 \
    -e RAGPIPE_ADMIN_TOKEN=ragpipe-admin-token \
    -e RAGSTUFFER_URL=http://localhost:8091 \
    -e RAGSTUFFER_MPEP_URL=http://localhost:8093 \
    -e QDRANT_URL=http://localhost:6333 \
    ghcr.io/aclater/ragdeck:main
```

## Quick start (pip)

```bash
pip install git+https://github.com/aclater/ragdeck
ragdeck
```

Or:

```bash
git clone https://github.com/aclater/ragdeck
cd ragdeck
pip install '.[dev]'
python -m pytest tests/ -v
```

## Backend API

All endpoints require `RAGDECK_ADMIN_TOKEN` bearer authentication unless noted.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health` | No | Returns `{"status": "ok"}` |
| `GET` | `/admin/config` | Yes | Returns ragpipe routing and prompt configuration |
| `GET` | `/collections` | Yes | List all Qdrant collections with stats |
| `GET` | `/collections/{name}` | Yes | Get specific collection details |
| `GET` | `/ingest/status` | Yes | ragstuffer ingest job status |
| `GET` | `/querylog` | Yes | Search ragpipe query log |
| `GET` | `/querylog/{query_hash}` | Yes | Get specific query log entry |
| `GET` | `/metrics` | Yes | Prometheus metrics from ragwatch |

## Frontend pages

| Route | Description |
|-------|-------------|
| `/` | Dashboard overview |
| `/collections` | Qdrant collection browser |
| `/ingest` | Ingest job monitor |
| `/querylog` | Query log viewer with search |
| `/metrics` | Real-time metrics dashboard |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8092` | Port to listen on |
| `RAGDECK_ADMIN_TOKEN` | *(required)* | Bearer token for admin authentication |
| `RAGPIPE_URL` | `http://localhost:8090` | ragpipe API URL |
| `RAGPIPE_ADMIN_TOKEN` | *(required)* | Token for ragpipe admin endpoints |
| `RAGSTUFFER_URL` | `http://localhost:8091` | ragstuffer API URL |
| `RAGSTUFFER_MPEP_URL` | `http://localhost:8093` | ragstuffer-mpep API URL |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant API URL |

## Running tests

```bash
pip install '.[dev]'
python -m pytest tests/ -v    # 24 tests
ruff check && ruff format --check
```

## Project structure

```
ragdeck/
  __init__.py      — empty (package marker)
  main.py          — FastAPI app with all endpoints and page routes
  static/
    app.js         — frontend JavaScript
    style.css      — frontend styles
  templates/
    base.html      — base template
    admin.html     — admin config page
    collections.html — collection browser
    dashboard.html — overview dashboard
    ingest.html    — ingest monitor
    metrics.html   — metrics dashboard
    querylog.html  — query log viewer
tests/
  test_auth.py     — authentication tests
  test_collections.py — collection endpoint tests
  test_health.py   — health endpoint tests
  test_metrics.py  — metrics endpoint tests
  test_querylog.py — query log endpoint tests
  test_service_unavailable.py — error handling tests
quadlets/
  ragdeck.container — Podman quadlet for systemd integration
```

## License

AGPL-3.0-or-later
