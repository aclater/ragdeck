# ragdeck

Admin UI for the rag-suite stack. Single-pane management for all services — collections, ingest, query log, probe runs, metrics.

## Status

**Production — fully implemented.** FastAPI backend with multiple endpoints, vanilla HTML/JS/CSS frontend with multiple pages, container image published to GHCR.

## Architecture
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
```

## Backend endpoints

All endpoints require `RAGDECK_ADMIN_TOKEN` bearer authentication unless noted.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health` | No | Returns `{"status": "ok"}` |
| `GET` | `/admin/config` | Yes | ragpipe routing and prompt config |
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

## Package structure
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
  ragdeck.container — admin UI service quadlet
```

## Key design decisions
- FastAPI backend for async API calls to all rag-suite services
- Single-pane admin UI — one endpoint to manage the entire stack
- No GPU required — pure API orchestration and UI rendering
- Port 8092 (configured in main.py)
- Authentication via `RAGDECK_ADMIN_TOKEN` bearer token

## Running tests
```bash
pip install '.[dev]'
python -m pytest tests/ -v    # 24 tests
ruff check && ruff format --check
```
