# ragdeck

Admin UI for the rag-suite stack. Single-pane management for all services — collections, ingest, query log, probe runs, metrics.

## Status

**Scaffold — under active development.**

Currently implemented:
- `/health` — returns `{"status": "ok"}`

Planned (not yet implemented):
- Collections browser — Qdrant collection management
- Ingest monitor — ragstuffer job status and manual trigger
- Query log viewer — ragpipe query_log search and filter
- Probe runs dashboard — ragprobe test results
- Metrics dashboard — ragwatch/Prometheus integration

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

## Package structure
```
ragdeck/
  __init__.py      — empty (package marker)
  main.py          — FastAPI app (health endpoint only currently)
tests/
  test_main.py     — stub test for /health
quadlets/
  ragdeck.container — admin UI service quadlet (stub)
```

## Key design decisions
- FastAPI backend for async API calls to all rag-suite services
- Single-pane admin UI — one endpoint to manage the entire stack
- No GPU required — pure API orchestration and UI rendering
- Port 8095 (configured in main.py, not 8092)

## Running tests
```bash
pip install '.[dev]'
python -m pytest tests/ -v
ruff check && ruff format --check
```
