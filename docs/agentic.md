# Agentic Observability

ragdeck surfaces ragorchestrator agentic query behavior through two API endpoints and the query log's agentic columns.

## Requirements

Agentic observability requires:
- **ragorchestrator** deployed and healthy (`GET /health` returns 200)
- **query_log table** in Postgres with `query_rewritten` and `retrieval_attempts` columns
- These columns are populated by ragorchestrator on every agentic query

When these are not available, `/agentic/stats` returns `{"status": "unavailable", "error": "Agentic columns not available in query_log schema"}`.

## Endpoints

### `GET /agentic/stats`

Aggregate agentic metrics across all queries.

```bash
curl -H "Authorization: Bearer $RAGDECK_ADMIN_TOKEN" \
  http://localhost:8092/agentic/stats
```

Response fields:
- `total_queries` — total queries in the query log
- `crag_retries` — count of queries where `query_rewritten = TRUE` (query was rewritten by CRAG)
- `crag_retry_rate` — `crag_retries / total_queries` (proportion of queries requiring rewrite)
- `avg_retrieval_attempts` — average number of retrieval passes per query
- `ragorchestrator_up` — whether ragorchestrator is reachable
- `complexity_distribution` — placeholder: always `{"simple": 0, "complex": 0, "external": 0}` (not yet implemented in ragorchestrator)

### `GET /agentic/traces/{query_hash}`

Full agentic trace for a single query.

```bash
curl -H "Authorization: Bearer $RAGDECK_ADMIN_TOKEN" \
  http://localhost:8092/agentic/traces/a1b2c3d4...
```

Response includes:
- `query_hash`, `grounding`, `latency_ms`, `created_at`
- `query_rewritten` — whether CRAG triggered a rewrite
- `retrieval_attempts` — number of retrieval passes
- `reflection_result` — `grounded` or `not_applicable`
- `ragorchestrator_trace` — full trace from ragorchestrator (when available)

## CRAG (Corrective RAG)

CRAG activates when ragorchestrator's Self-RAG reflection loop determines the initial retrieval results are insufficient. When this happens:

1. The query is rewritten with more specific terms
2. `query_rewritten` is set to `TRUE` in the query log
3. A new retrieval pass is executed
4. Final results are grounded and returned

The `crag_retry_rate` metric tracks how often this happens — a high rate may indicate:
- Chunking strategy needs tuning
- Collection is missing relevant documents
- Query complexity exceeds retrieval effectiveness

## Self-RAG Reflection

ragorchestrator uses Self-RAG (Self-Reflective RAG) to evaluate each retrieval pass:

1. **Is the passage relevant?** — Score 0-1 from reflection LLM
2. **Is the response grounded?** — Did it use the retrieved passages?
3. **Is the answer useful?** — Would it answer the user's question?

The reflection loop runs up to `MAX_RETRIEVAL_PASSES` (configured in ragorchestrator) until all three criteria are met, or max passes is reached.

## Complexity Classification

ragorchestrator classifies each query into:
- **simple** — direct lookup, single retrieval pass
- **complex** — requires multi-hop reasoning or multiple retrieval passes
- **external** — requires web search (when Tavily is configured)

Complexity classification metrics are tracked in ragorchestrator Prometheus metrics.

## Integration with Dashboard

The query log UI (`/querylog-ui`) shows `query_rewritten` and `retrieval_attempts` columns when agentic columns are present in the Postgres schema. These are displayed as colored badges and numeric values respectively.

## Linking to ragorchestrator

ragdeck proxies trace requests to ragorchestrator at `GET /traces/{query_hash}`. If ragorchestrator returns a trace, it is embedded in the `ragorchestrator_trace` field of the trace response.
