# ragdeck

Admin UI for the rag-suite stack. Single-pane management for all services — collections, ingest, query log, probe runs, metrics.

## What it does

ragdeck is the administrative control plane for the rag-suite. It provides a unified interface to:

- **Collections** — browse, create, and manage Qdrant collections across all routes
- **Ingest** — monitor ragstuffer job status, trigger manual ingestion, view processing queues
- **Query log** — search and filter the ragpipe query log, inspect grounding decisions and citations
- **Probe runs** — view ragprobe test results, track grounding quality over time, detect regressions
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

## Running tests

```bash
pip install '.[dev]'
python -m pytest tests/ -v
ruff check && ruff format --check
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8095` | Port to listen on |

## Status

**Under active development — scaffold.** Currently implemented:

- `/health` — returns `{"status": "ok"}`

Planned (not yet implemented):

- Collections browser — Qdrant collection management
- Ingest monitor — ragstuffer job status and manual trigger
- Query log viewer — ragpipe query_log search and filter
- Probe runs dashboard — ragprobe test results
- Metrics dashboard — ragwatch/Prometheus integration

## Project structure

```
ragdeck/
  __init__.py      — empty (package marker)
  main.py          — FastAPI app (health endpoint only, currently)
tests/
  test_main.py     — stub test for /health
quadlets/
  ragdeck.container — admin UI service quadlet (stub)
```

## License

AGPL-3.0-or-later
