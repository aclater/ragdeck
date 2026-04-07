# API Reference

All endpoints require `RAGDECK_ADMIN_TOKEN` bearer authentication unless noted.

## Health & Status

### `GET /health`

No auth required. Returns service health.

```bash
curl http://localhost:8092/health
```
```json
{"status": "ok"}
```

### `GET /status`

Returns status of all rag-suite services.

```bash
curl -H "Authorization: Bearer $RAGDECK_ADMIN_TOKEN" \
  http://localhost:8092/status
```
```json
{
  "status": "ok",
  "services": {
    "ragpipe": {"status": "up", "url": "http://localhost:8090"},
    "ragstuffer": {"status": "up", "url": "http://localhost:8091"},
    "ragwatch": {"status": "up", "url": "http://localhost:9090"},
    "ragorchestrator": {"status": "up", "url": "http://localhost:8095"},
    "qdrant": {"status": "up", "url": "http://localhost:6333"},
    "postgres": {"status": "up"}
  }
}
```

## Collections

### `GET /collections`

List all Qdrant collections with stats.

```bash
curl -H "Authorization: Bearer $RAGDECK_ADMIN_TOKEN" \
  http://localhost:8092/collections
```
```json
{
  "collections": [
    {
      "id": "uuid",
      "name": "personnel",
      "description": "...",
      "source_types": "[\"drive\",\"git\"]",
      "created_at": "2025-01-15T10:30:00",
      "vector_count": 14250
    }
  ]
}
```

### `GET /collections/{name}`

Get specific collection details including Qdrant point counts.

```bash
curl -H "Authorization: Bearer $RAGDECK_ADMIN_TOKEN" \
  http://localhost:8092/collections/personnel
```

### `POST /collections`

Create a new collection. Creates entry in both Postgres and Qdrant.

```bash
curl -X POST -H "Authorization: Bearer $RAGDECK_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "mypep", "description": "MPEP patent manual"}' \
  http://localhost:8092/collections
```

### `DELETE /collections/{name}`

Delete a collection from both Postgres and Qdrant.

```bash
curl -X DELETE -H "Authorization: Bearer $RAGDECK_ADMIN_TOKEN" \
  http://localhost:8092/collections/personnel
```

## Ingest

### `GET /ingest/status`

Ragstuffer ingest job status and collection last-updated times.

```bash
curl -H "Authorization: Bearer $RAGDECK_ADMIN_TOKEN" \
  http://localhost:8092/ingest/status
```
```json
{
  "ragstuffer_up": true,
  "collections": [
    {"name": "personnel", "source_types": "[\"drive\"]", "last_updated": "2025-01-20T14:00:00"}
  ]
}
```

### `POST /ingest/trigger`

Trigger incremental ragstuffer ingest (Drive delta, git diff).

```bash
curl -X POST -H "Authorization: Bearer $RAGDECK_ADMIN_TOKEN" \
  http://localhost:8092/ingest/trigger
```

### `POST /ingest/trigger-full`

Trigger full ragstuffer ingest (complete Drive scan, full git clone).

```bash
curl -X POST -H "Authorization: Bearer $RAGDECK_ADMIN_TOKEN" \
  http://localhost:8092/ingest/trigger-full
```

### `GET /ingest/history`

Recent ingest history per collection.

```bash
curl -H "Authorization: Bearer $RAGDECK_ADMIN_TOKEN" \
  "http://localhost:8092/ingest/history?limit=10"
```

## Query Log

### `GET /querylog`

Search and paginate the ragpipe query log.

```bash
curl -H "Authorization: Bearer $RAGDECK_ADMIN_TOKEN" \
  "http://localhost:8092/querylog?limit=20&offset=0&grounding=corpus"
```

Query parameters:
- `limit` (default 20, max 100)
- `offset` (default 0)
- `grounding` (optional: `corpus`, `general`, `mixed`)

### `GET /querylog/stats`

Query log statistics grouped by grounding type.

```bash
curl -H "Authorization: Bearer $RAGDECK_ADMIN_TOKEN" \
  http://localhost:8092/querylog/stats
```
```json
{
  "total": 142,
  "by_grounding": {
    "corpus": {"count": 89, "avg_latency": 234.5},
    "general": {"count": 41, "avg_latency": 156.2},
    "mixed": {"count": 12, "avg_latency": 412.8}
  }
}
```

### `GET /querylog/{query_hash}`

Get a specific query log entry by hash.

```bash
curl -H "Authorization: Bearer $RAGDECK_ADMIN_TOKEN" \
  http://localhost:8092/querylog/a1b2c3d4...
```

## Agentic Observability

### `GET /agentic/stats`

Agentic query behavior metrics from ragorchestrator. Requires `query_rewritten` and `retrieval_attempts` columns in query_log.

```bash
curl -H "Authorization: Bearer $RAGDECK_ADMIN_TOKEN" \
  http://localhost:8092/agentic/stats
```
```json
{
  "total_queries": 142,
  "crag_retries": 23,
  "crag_retry_rate": 0.162,
  "avg_retrieval_attempts": 1.3,
  "ragorchestrator_up": true,
  "complexity_distribution": {"simple": 0, "complex": 0, "external": 0}
}
```

Returns `{"status": "unavailable", "error": "Agentic columns not available..."}` when ragorchestrator is not deployed.

### `GET /agentic/traces/{query_hash}`

Full agentic trace for a single query including ragorchestrator reflection data.

```bash
curl -H "Authorization: Bearer $RAGDECK_ADMIN_TOKEN" \
  http://localhost:8092/agentic/traces/a1b2c3d4...
```

## Metrics

### `GET /metrics`

Proxy to ragwatch `/metrics/summary` — structured Prometheus metrics summary.

```bash
curl -H "Authorization: Bearer $RAGDECK_ADMIN_TOKEN" \
  http://localhost:8092/metrics
```
```json
{
  "status": "up",
  "sources": {
    "ragpipe": {"up": true, "metric_count": 27},
    "ragstuffer": {"up": true, "metric_count": 4},
    "ragorchestrator": {"up": true, "metric_count": 38}
  },
  "ragpipe": {"queries_total": 142.0, "embed_cache_hit_rate": 0.87, ...},
  "ragstuffer": {"documents_ingested_total": 342.0, ...},
  "ragorchestrator": {"queries_total": 89.0, ...}
}
```

### `GET /metrics/ragpipe`

Raw Prometheus metrics text from ragpipe.

```bash
curl -H "Authorization: Bearer $RAGDECK_ADMIN_TOKEN" \
  http://localhost:8092/metrics/ragpipe
```

### `GET /metrics/ragstuffer`

Raw Prometheus metrics text from ragstuffer.

```bash
curl -H "Authorization: Bearer $RAGDECK_ADMIN_TOKEN" \
  http://localhost:8092/metrics/ragstuffer
```

### `GET /metrics/ragorchestrator`

Raw Prometheus metrics text from ragorchestrator.

```bash
curl -H "Authorization: Bearer $RAGDECK_ADMIN_TOKEN" \
  http://localhost:8092/metrics/ragorchestrator
```

## Admin

### `GET /admin/config`

Get ragpipe routing and prompt configuration.

```bash
curl -H "Authorization: Bearer $RAGDECK_ADMIN_TOKEN" \
  http://localhost:8092/admin/config
```

### `POST /admin/reload-routes`

Hot-reload ragpipe routing rules without restart.

```bash
curl -X POST \
  -H "Authorization: Bearer $RAGDECK_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ragpipe_admin_token": "..."}' \
  http://localhost:8092/admin/reload-routes
```

### `POST /admin/reload-prompt`

Hot-reload ragpipe system prompt without restart.

```bash
curl -X POST \
  -H "Authorization: Bearer $RAGDECK_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ragpipe_admin_token": "..."}' \
  http://localhost:8092/admin/reload-prompt
```

## UI Page Routes

UI pages are rendered as HTML (no auth on the HTML itself; API calls within the page require auth).

| Route | Description |
|-------|-------------|
| `GET /` | Dashboard overview |
| `GET /collections-ui` | Qdrant collection browser |
| `GET /ingest-ui` | Ingest job monitor |
| `GET /querylog-ui` | Query log viewer |
| `GET /metrics-ui` | Real-time metrics dashboard |
| `GET /admin-ui` | ragpipe admin config |
