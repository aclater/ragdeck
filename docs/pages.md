# UI Pages

ragdeck provides six frontend pages, all accessible at `/<name>-ui` (e.g. `/collections-ui`).

## Dashboard (`/`)

Overview of the entire rag-suite stack.

**Service health tiles** — one per service (ragpipe, ragstuffer, ragorchestrator, ragwatch, Qdrant, Postgres) showing live up/down status. Refreshes every 30 seconds.

**Summary tiles** — total collections, queries today, corpus grounding rate, average latency.

**Grounding distribution** — donut chart showing proportion of corpus/general/mixed queries from the query log.

**Recent queries table** — last 10 queries with time, grounding badge, latency, and cited chunk count. Click any row to inspect the full query entry.

## Collections (`/collections-ui`)

Browse all Qdrant collections registered in Postgres.

**Collection list** — table with name, vector count, source types, and created date.

**Actions per row:**
- **View** — opens a detail panel showing collection ID, description, Qdrant vector/point counts, source types, and created timestamp.
- **Delete** — removes the collection from both Postgres and Qdrant (with confirmation dialog).

**Create collection** — form at the top to register a new collection. Creates entry in Postgres and Qdrant simultaneously.

## Ingest (`/ingest-ui`)

Monitor ragstuffer ingest jobs and collection freshness.

**Ragstuffer status** — up/down badge for ragstuffer service.

**Collection table** — each registered collection with source types and last-updated timestamp.

**Trigger buttons:**
- **Ingest Now** — triggers incremental ingest (Drive delta, git diff only)
- **Ingest Full** — triggers full re-ingest (complete Drive scan, full git clone)

Requires `RAGSTUFFER_ADMIN_TOKEN` configured in the environment.

## Query Log (`/querylog-ui`)

Searchable, paginated view of all ragpipe queries.

**Filter bar** — filter by grounding type (corpus, general, mixed) or view all.

**Query table** — columns: Time, Grounding (colored badge), Latency, Cited chunks, Hash (truncated).

**Click any row** — opens an expandable detail panel showing:
- Full query hash
- Grounding type badge
- Latency in milliseconds
- Timestamp
- List of cited chunks as JSON

**Pagination** — 20 entries per page with prev/next navigation.

## Metrics (`/metrics-ui`)

Real-time Prometheus metrics from ragwatch, rendered as structured cards.

**Service health tiles** — ragpipe, ragstuffer, ragorchestrator with up/down status and metric count.

**ragpipe metrics** — Queries, Cache Hits, Cache Misses, Cache Hit Rate, Invalid Citations, Chunks Retrieved.

**ragstuffer metrics** — Documents Ingested, Chunks Created, Embed Requests, Embed Errors.

**ragorchestrator metrics** — Queries, Avg Latency, Tool Calls, Complexity Classifications.

**Raw JSON toggle** — collapsed by default; click Show/Hide to inspect the full ragwatch response for debugging.

Auto-refreshes every 60 seconds. Gracefully shows an error message if ragwatch is unavailable.

## Admin (`/admin-ui`)

ragpipe routing and prompt configuration viewer.

**Current config** — displays the live ragpipe `/admin/config` response as JSON.

**Actions:**
- **Reload Routes** — hot-reloads ragpipe routing rules via `POST /admin/reload-routes`
- **Reload Prompt** — hot-reloads the system prompt via `POST /admin/reload-prompt`

Both actions require `RAGPIPE_ADMIN_TOKEN`. Results shown inline without page refresh.
