# ragdeck

Admin UI for the rag-suite stack. Single-pane management for all services — collections, ingest, query log, probe runs, metrics.

## What it does

ragdeck is the administrative control plane for the rag-suite:

- **Collections** — browse Qdrant collections, view vector counts, create and delete
- **Ingest** — monitor ragstuffer job status, trigger incremental or full ingest
- **Query log** — search and filter the ragpipe query log, inspect grounding decisions and citations
- **Metrics** — real-time structured dashboards powered by ragwatch (Prometheus)
- **Admin** — view and hot-reload ragpipe routing and system prompt

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
   │         │ │  er    │ │       │ │         │
   └─────────┘ └────────┘ └───────┘ └─────────┘
```

## Quick start (container)

```bash
podman run --rm -p 8092:8092 \
    -e RAGDECK_ADMIN_TOKEN=your-secure-token \
    -e DOCSTORE_URL=postgresql://user:pass@host:5432/ragdeck \
    ghcr.io/aclater/ragdeck:main
```

## Quick start (pip)

```bash
pip install git+https://github.com/aclater/ragdeck
ragdeck
```

## Documentation

| Doc | Description |
|-----|-------------|
| [docs/api.md](docs/api.md) | Full API endpoint reference with curl examples |
| [docs/pages.md](docs/pages.md) | Frontend page guide (dashboard, collections, ingest, query log, metrics, admin) |
| [docs/configuration.md](docs/configuration.md) | All environment variables with defaults |
| [docs/agentic.md](docs/agentic.md) | Agentic observability: CRAG metrics, Self-RAG, complexity classification |

## Running tests

```bash
pip install '.[dev]'
python -m pytest tests/ -v    # 53 tests
ruff check && ruff format --check
```

## License

AGPL-3.0-or-later
