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

## Status

Under active development. Only a health endpoint is implemented — this is a scaffold.

## License

AGPL-3.0-or-later
