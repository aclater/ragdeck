"""ragdeck — admin UI for the rag-suite stack.

Provides a unified admin interface to all rag-suite services:
ragpipe, ragstuffer, ragwatch, Qdrant, and Postgres.
"""

import asyncio
import os
from contextlib import asynccontextmanager

import asyncpg
import httpx
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

RAGPIPE_URL = os.environ.get("RAGPIPE_URL", "http://host.containers.internal:8090")
RAGSTUFFER_URL = os.environ.get("RAGSTUFFER_URL", "http://host.containers.internal:8091")
RAGWATCH_URL = os.environ.get("RAGWATCH_URL", "http://host.containers.internal:9090")
RAGORCHESTRATOR_URL = os.environ.get("RAGORCHESTRATOR_URL", "http://host.containers.internal:8095")
QDRANT_URL = os.environ.get("QDRANT_URL", "http://host.containers.internal:6333")
DOCSTORE_URL = os.environ.get("DOCSTORE_URL", "")
ADMIN_TOKEN = os.environ.get("RAGDECK_ADMIN_TOKEN", "")

HTTP_TIMEOUT = 10.0

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        if not DOCSTORE_URL:
            raise RuntimeError("DOCSTORE_URL not set")
        _pool = await asyncpg.create_pool(DOCSTORE_URL, min_size=1, max_size=5)
    return _pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


app = FastAPI(
    title="ragdeck",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

templates = Jinja2Templates(directory="ragdeck/templates")
app.mount("/static", StaticFiles(directory="ragdeck/static"), name="static")


class UnavailableError(BaseModel):
    status: str = "unavailable"
    error: str


def _check_service(url: str, path: str = "/health") -> tuple[str, dict]:
    async def check():
        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                resp = await client.get(f"{url}{path}")
                return {"status": "up" if resp.status_code == 200 else "down", "url": url}
        except Exception as e:
            return {"status": "down", "url": url, "error": str(e)}

    return url, check()


async def _check_ragpipe():
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            resp = await client.get(f"{RAGPIPE_URL}/health")
            return {"status": "up" if resp.status_code == 200 else "down", "url": RAGPIPE_URL}
    except Exception as e:
        return {"status": "down", "url": RAGPIPE_URL, "error": str(e)}


async def _check_ragstuffer():
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            resp = await client.get(f"{RAGSTUFFER_URL}/health")
            return {"status": "up" if resp.status_code == 200 else "down", "url": RAGSTUFFER_URL}
    except Exception as e:
        return {"status": "down", "url": RAGSTUFFER_URL, "error": str(e)}


async def _check_ragwatch():
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            resp = await client.get(f"{RAGWATCH_URL}/health")
            return {"status": "up" if resp.status_code == 200 else "down", "url": RAGWATCH_URL}
    except Exception as e:
        return {"status": "down", "url": RAGWATCH_URL, "error": str(e)}


async def _check_ragorchestrator():
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            resp = await client.get(f"{RAGORCHESTRATOR_URL}/health")
            return {"status": "up" if resp.status_code == 200 else "down", "url": RAGORCHESTRATOR_URL}
    except Exception as e:
        return {"status": "down", "url": RAGORCHESTRATOR_URL, "error": str(e)}


async def _check_qdrant():
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            resp = await client.get(f"{QDRANT_URL}/collections")
            return {"status": "up" if resp.status_code == 200 else "down", "url": QDRANT_URL}
    except Exception as e:
        return {"status": "down", "url": QDRANT_URL, "error": str(e)}


async def _check_postgres():
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "up"}
    except Exception as e:
        return {"status": "down", "error": str(e)}


async def _proxy_ragpipe(path: str, method: str = "GET", token: str = "", json_body: dict | None = None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            func = getattr(client, method.lower())
            kwargs = {"headers": headers}
            if json_body:
                kwargs["json"] = json_body
            resp = await func(f"{RAGPIPE_URL}{path}", **kwargs)
            try:
                data = resp.json()
            except Exception:
                data = {"raw": resp.text}
            return {**data, "_status": resp.status_code}
    except Exception as e:
        return {"error": str(e), "_status": 0}


# ── Health & Status ────────────────────────────────────────────────────────────


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/status")
async def status():
    pipe, stuffer, watch, orch, qdrant, pg = await asyncio.gather(
        _check_ragpipe(),
        _check_ragstuffer(),
        _check_ragwatch(),
        _check_ragorchestrator(),
        _check_qdrant(),
        _check_postgres(),
    )
    all_up = all(s.get("status") == "up" for s in [pipe, stuffer, qdrant, pg])
    return {
        "status": "ok" if all_up else "degraded",
        "services": {
            "ragpipe": pipe,
            "ragstuffer": stuffer,
            "ragwatch": watch,
            "ragorchestrator": orch,
            "qdrant": qdrant,
            "postgres": pg,
        },
    }


# ── Collections ─────────────────────────────────────────────────────────────────


@app.get("/collections")
async def list_collections():
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, name, description, source_types, created_at FROM collections ORDER BY created_at DESC"
            )

        collections = [
            {
                "id": str(row["id"]),
                "name": row["name"],
                "description": row["description"] or "",
                "source_types": row["source_types"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            }
            for row in rows
        ]

        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                resp = await client.get(f"{QDRANT_URL}/collections")
                if resp.status_code == 200:
                    data = resp.json()
                    vector_counts = {
                        c["name"]: c.get("vectors_count", 0) for c in data.get("result", {}).get("collections", [])
                    }
                    for col in collections:
                        col["vector_count"] = vector_counts.get(col["name"], 0)
                else:
                    for col in collections:
                        col["vector_count"] = None
        except Exception:
            for col in collections:
                col["vector_count"] = None

        return {"collections": collections}
    except Exception as e:
        return UnavailableError(error=str(e))


@app.post("/collections")
async def create_collection(request: Request):
    auth = request.headers.get("Authorization", "")
    if not ADMIN_TOKEN or f"Bearer {ADMIN_TOKEN}" != auth:
        raise HTTPException(status_code=401, detail="Unauthorized")
    body = await request.json()
    name = body.get("name", "").strip()
    description = body.get("description", "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name is required")

    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            collection_id = str(
                await conn.fetchval(
                    """
                    INSERT INTO collections (id, name, description, source_types, created_at, updated_at)
                    VALUES (gen_random_uuid(), $1, $2, $3, now(), now())
                    ON CONFLICT (name) DO UPDATE SET description = $2, updated_at = now()
                    RETURNING id
                    """,
                    name,
                    description,
                    "[]",
                )
            )

        vector_size = int(os.environ.get("QDRANT_VECTOR_SIZE", "768"))
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            try:
                resp = await client.put(
                    f"{QDRANT_URL}/collections/{name}",
                    json={"vectors": {"size": vector_size, "distance": "Cosine"}},
                )
                if resp.status_code not in (200, 201):
                    return {"warning": f"Collection saved but Qdrant error: {resp.status_code}"}
            except Exception as e:
                return {"warning": f"Collection saved but Qdrant error: {str(e)}"}

        return {"status": "ok", "name": name, "id": collection_id}
    except Exception as e:
        return UnavailableError(error=str(e))


@app.get("/collections/{name}")
async def get_collection(name: str):
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, name, description, source_types, created_at FROM collections WHERE name = $1",
                name,
            )
        if not row:
            raise HTTPException(status_code=404, detail="Collection not found")

        vector_count = None
        points_count = None
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            try:
                resp = await client.get(f"{QDRANT_URL}/collections/{name}")
                if resp.status_code == 200:
                    data = resp.json()
                    info = data.get("result", {})
                    vector_count = info.get("vectors_count", 0)
                    points_count = info.get("points_count", 0)
            except Exception:
                pass

        return {
            "id": str(row["id"]),
            "name": row["name"],
            "description": row["description"] or "",
            "source_types": row["source_types"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "vector_count": vector_count,
            "points_count": points_count,
        }
    except HTTPException:
        raise
    except Exception as e:
        return UnavailableError(error=str(e))


@app.delete("/collections/{name}")
async def delete_collection(name: str, request: Request):
    auth = request.headers.get("Authorization", "")
    if not ADMIN_TOKEN or f"Bearer {ADMIN_TOKEN}" != auth:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM collections WHERE name = $1", name)

        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            try:
                await client.delete(f"{QDRANT_URL}/collections/{name}")
            except Exception:
                pass

        return {"status": "ok", "name": name}
    except Exception as e:
        return UnavailableError(error=str(e))


# ── Ingest ──────────────────────────────────────────────────────────────────────


@app.get("/ingest/status")
async def ingest_status():
    try:
        ragstuffer_up = False
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            try:
                resp = await client.get(f"{RAGSTUFFER_URL}/health")
                ragstuffer_up = resp.status_code == 200
            except Exception:
                pass

        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT name, source_types, updated_at FROM collections ORDER BY updated_at DESC")

        return {
            "ragstuffer_up": ragstuffer_up,
            "collections": [
                {
                    "name": r["name"],
                    "source_types": r["source_types"],
                    "last_updated": r["updated_at"].isoformat() if r["updated_at"] else None,
                }
                for r in rows
            ],
        }
    except Exception as e:
        return UnavailableError(error=str(e))


@app.post("/ingest/trigger")
async def trigger_ingest(request: Request):
    auth = request.headers.get("Authorization", "")
    if not ADMIN_TOKEN or f"Bearer {ADMIN_TOKEN}" != auth:
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = os.environ.get("RAGSTUFFER_ADMIN_TOKEN", "")
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            resp = await client.post(f"{RAGSTUFFER_URL}/admin/ingest-now", headers=headers)
            if resp.status_code == 200:
                return resp.json()
            return {"error": f"HTTP {resp.status_code}", "detail": resp.text}
    except Exception as e:
        return {"error": str(e)}


@app.post("/ingest/trigger-full")
async def trigger_ingest_full(request: Request):
    auth = request.headers.get("Authorization", "")
    if not ADMIN_TOKEN or f"Bearer {ADMIN_TOKEN}" != auth:
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = os.environ.get("RAGSTUFFER_ADMIN_TOKEN", "")
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            resp = await client.post(f"{RAGSTUFFER_URL}/admin/ingest-full", headers=headers)
            if resp.status_code == 200:
                return resp.json()
            return {"error": f"HTTP {resp.status_code}", "detail": resp.text}
    except Exception as e:
        return {"error": str(e)}


@app.get("/ingest/history")
async def ingest_history(limit: int = Query(default=20, le=100)):
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT DISTINCT ON (name) name, source_types, updated_at
                FROM collections
                ORDER BY name, updated_at DESC
                LIMIT $1
                """,
                limit,
            )
        return {
            "history": [
                {
                    "collection": r["name"],
                    "source_types": r["source_types"],
                    "last_updated": r["updated_at"].isoformat() if r["updated_at"] else None,
                }
                for r in rows
            ]
        }
    except Exception as e:
        return UnavailableError(error=str(e))


# ── Query Log ──────────────────────────────────────────────────────────────────


async def _check_column_exists(conn, table: str, column: str) -> bool:
    try:
        await conn.fetchval(f'SELECT 1 FROM "{table}" WHERE FALSE LIMIT 1')
        return False
    except Exception:
        pass
    try:
        await conn.fetchval(f'SELECT {column} FROM "{table}" LIMIT 1')
        return True
    except Exception:
        return False


async def _proxy_ragorchestrator(path: str, method: str = "GET", token: str = "", json_body: dict | None = None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            func = getattr(client, method.lower())
            kwargs = {"headers": headers}
            if json_body:
                kwargs["json"] = json_body
            resp = await func(f"{RAGORCHESTRATOR_URL}{path}", **kwargs)
            try:
                data = resp.json()
            except Exception:
                data = {"raw": resp.text}
            return {**data, "_status": resp.status_code}
    except Exception as e:
        return {"error": str(e), "_status": 0}


@app.get("/querylog")
async def get_querylog(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    grounding: str | None = None,
):
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            has_agentic_cols = await _check_column_exists(conn, "query_log", "retrieval_attempts")

            base_cols = "query_hash, grounding, cited_chunks, latency_ms, created_at"
            agentic_cols = ", query_rewritten, retrieval_attempts"
            all_cols = base_cols + agentic_cols if has_agentic_cols else base_cols

            if grounding:
                rows = await conn.fetch(
                    f"""
                    SELECT {all_cols}
                    FROM query_log
                    WHERE grounding = $3
                    ORDER BY created_at DESC
                    LIMIT $1 OFFSET $2
                    """,
                    limit,
                    offset,
                    grounding,
                )
                total = await conn.fetchval("SELECT COUNT(*) FROM query_log WHERE grounding = $1", grounding)
            else:
                rows = await conn.fetch(
                    f"""
                    SELECT {all_cols}
                    FROM query_log
                    ORDER BY created_at DESC
                    LIMIT $1 OFFSET $2
                    """,
                    limit,
                    offset,
                )
                total = await conn.fetchval("SELECT COUNT(*) FROM query_log")

            entries = []
            for r in rows:
                entry = {
                    "query_hash": r["query_hash"],
                    "grounding": r["grounding"],
                    "cited_chunks": list(r["cited_chunks"]) if r["cited_chunks"] else [],
                    "latency_ms": r["latency_ms"],
                    "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                }
                if has_agentic_cols:
                    entry["query_rewritten"] = r.get("query_rewritten")
                    entry["retrieval_attempts"] = r.get("retrieval_attempts")
                entries.append(entry)

        return {
            "entries": entries,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        return UnavailableError(error=str(e))


@app.get("/querylog/stats")
async def get_querylog_stats():
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT grounding, COUNT(*) as count, AVG(latency_ms) as avg_latency
                FROM query_log
                GROUP BY grounding
                """
            )
            total = await conn.fetchval("SELECT COUNT(*) FROM query_log")

        return {
            "total": total,
            "by_grounding": {
                r["grounding"]: {
                    "count": r["count"],
                    "avg_latency": float(r["avg_latency"]) if r["avg_latency"] else None,
                }
                for r in rows
            },
        }
    except Exception as e:
        return UnavailableError(error=str(e))


@app.get("/querylog/{query_hash}")
async def get_querylog_entry(query_hash: str):
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT query_hash, grounding, cited_chunks, latency_ms, created_at
                FROM query_log WHERE query_hash = $1
                """,
                query_hash,
            )
        if not row:
            raise HTTPException(status_code=404, detail="Query log entry not found")
        return {
            "query_hash": row["query_hash"],
            "grounding": row["grounding"],
            "cited_chunks": list(row["cited_chunks"]) if row["cited_chunks"] else [],
            "latency_ms": row["latency_ms"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        return UnavailableError(error=str(e))


# ── Agentic Observability ───────────────────────────────────────────────────────


def _parse_prometheus_counter(text: str, metric_name: str, label: str) -> dict[str, float]:
    """Parse a Prometheus counter with labels into a dict of {label_value: count}.

    Example input:
        ragorchestrator_complexity_classified_total{complexity="simple"} 5.0
        ragorchestrator_complexity_classified_total{complexity="complex"} 2.0

    Returns: {"simple": 5.0, "complex": 2.0}
    """
    import re

    pattern = re.compile(
        rf'^{re.escape(metric_name)}\{{{re.escape(label)}="([^"]+)"\}}\s+([\d.eE+-]+)',
        re.MULTILINE,
    )
    return {m.group(1): float(m.group(2)) for m in pattern.finditer(text)}


async def _fetch_complexity_distribution() -> dict[str, int]:
    """Fetch complexity classification counts from ragorchestrator /metrics.

    Falls back to zeros if ragorchestrator is unreachable or metrics
    are not available.
    """
    default = {"simple": 0, "complex": 0, "external": 0}
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            resp = await client.get(f"{RAGORCHESTRATOR_URL}/metrics")
            if resp.status_code != 200:
                return default
            counts = _parse_prometheus_counter(
                resp.text,
                "ragorchestrator_complexity_classified_total",
                "complexity",
            )
            return {
                "simple": int(counts.get("simple", 0)),
                "complex": int(counts.get("complex", 0)),
                "external": int(counts.get("external", 0)),
            }
    except Exception:
        return default


@app.get("/agentic/stats")
async def get_agentic_stats():
    """Dashboard showing agentic query behavior metrics.

    Returns:
    - CRAG retry rate (% of queries that triggered rewrite)
    - Complexity distribution (simple/complex/external)
    - Average retrieval attempts
    - Self-RAG reflection loop rate
    """
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            has_agentic = await _check_column_exists(conn, "query_log", "query_rewritten")

            if not has_agentic:
                return {
                    "status": "unavailable",
                    "error": "Agentic columns not available in query_log schema",
                    "note": "ragorchestrator must be deployed to generate agentic metrics",
                }

            stats = {}

            total = await conn.fetchval("SELECT COUNT(*) FROM query_log")
            stats["total_queries"] = total

            rewritten = await conn.fetchval("SELECT COUNT(*) FROM query_log WHERE query_rewritten = TRUE")
            stats["crag_retries"] = rewritten
            stats["crag_retry_rate"] = rewritten / total if total > 0 else 0

            avg_retries = await conn.fetchval("SELECT COALESCE(AVG(retrieval_attempts), 1) FROM query_log")
            stats["avg_retrieval_attempts"] = float(avg_retries) if avg_retries else 1.0

            try:
                ragorch_up = False
                async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                    resp = await client.get(f"{RAGORCHESTRATOR_URL}/health")
                    ragorch_up = resp.status_code == 200
                stats["ragorchestrator_up"] = ragorch_up
            except Exception:
                stats["ragorchestrator_up"] = False

            stats["complexity_distribution"] = await _fetch_complexity_distribution()

            return stats
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/agentic/traces/{query_hash}")
async def get_agentic_trace(query_hash: str):
    """Full agentic trace for a single query.

    Returns:
    - Original query hash
    - Complexity classification
    - Sub-queries (if decomposed)
    - Each retrieval pass with scores
    - Reflection result
    - Final answer with grounding
    """
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT query_hash, grounding, cited_chunks, latency_ms, created_at,
                       query_rewritten, retrieval_attempts
                FROM query_log WHERE query_hash = $1
                """,
                query_hash,
            )

        if not row:
            raise HTTPException(status_code=404, detail="Query not found")

        trace = {
            "query_hash": row["query_hash"],
            "grounding": row["grounding"],
            "cited_chunks": list(row["cited_chunks"]) if row["cited_chunks"] else [],
            "latency_ms": row["latency_ms"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "query_rewritten": row.get("query_rewritten"),
            "retrieval_attempts": row.get("retrieval_attempts", 1),
            "ragorchestrator_trace": None,
        }

        if row.get("query_rewritten") is not None:
            trace["reflection_result"] = "grounded"
        else:
            trace["reflection_result"] = "not_applicable"

        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                resp = await client.get(f"{RAGORCHESTRATOR_URL}/traces/{query_hash}")
                if resp.status_code == 200:
                    trace["ragorchestrator_trace"] = resp.json()
                elif resp.status_code == 404:
                    trace["ragorchestrator_trace"] = {"status": "not_found"}
                else:
                    trace["ragorchestrator_trace"] = {"status": f"http_{resp.status_code}"}
        except Exception as e:
            trace["ragorchestrator_trace"] = {"status": "unavailable", "error": str(e)}

        return trace
    except HTTPException:
        raise
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ── Metrics ─────────────────────────────────────────────────────────────────────


@app.get("/metrics")
async def get_metrics():
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            resp = await client.get(f"{RAGWATCH_URL}/metrics/summary")
            if resp.status_code == 200:
                return resp.json()
            return {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/metrics/ragpipe")
async def get_ragpipe_metrics():
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            resp = await client.get(f"{RAGPIPE_URL}/metrics")
            if resp.status_code == 200:
                return {"metrics": resp.text}
            return {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/metrics/ragstuffer")
async def get_ragstuffer_metrics():
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            resp = await client.get(f"{RAGSTUFFER_URL}/metrics")
            if resp.status_code == 200:
                return {"metrics": resp.text}
            return {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/metrics/ragorchestrator")
async def get_ragorchestrator_metrics():
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            resp = await client.get(f"{RAGORCHESTRATOR_URL}/metrics")
            if resp.status_code == 200:
                return {"metrics": resp.text}
            return {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}


# ── Probe ───────────────────────────────────────────────────────────────────────


@app.get("/probe/results")
async def get_probe_results():
    return {"status": "unavailable", "error": "ragprobe not yet implemented"}


@app.post("/probe/run")
async def run_probe(request: Request):
    auth = request.headers.get("Authorization", "")
    if not ADMIN_TOKEN or f"Bearer {ADMIN_TOKEN}" != auth:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"status": "unavailable", "error": "ragprobe not yet implemented"}


# ── Admin ───────────────────────────────────────────────────────────────────────


@app.post("/admin/reload-routes")
async def admin_reload_routes(request: Request):
    auth = request.headers.get("Authorization", "")
    if not ADMIN_TOKEN or f"Bearer {ADMIN_TOKEN}" != auth:
        raise HTTPException(status_code=401, detail="Unauthorized")
    body = await request.json()
    token = body.get("ragpipe_admin_token", os.environ.get("RAGPIPE_ADMIN_TOKEN", ""))
    result = await _proxy_ragpipe("/admin/reload-routes", "POST", token)
    return result


@app.post("/admin/reload-prompt")
async def admin_reload_prompt(request: Request):
    auth = request.headers.get("Authorization", "")
    if not ADMIN_TOKEN or f"Bearer {ADMIN_TOKEN}" != auth:
        raise HTTPException(status_code=401, detail="Unauthorized")
    body = await request.json()
    token = body.get("ragpipe_admin_token", os.environ.get("RAGPIPE_ADMIN_TOKEN", ""))
    result = await _proxy_ragpipe("/admin/reload-prompt", "POST", token)
    return result


@app.get("/admin/config")
async def admin_config():
    token = os.environ.get("RAGPIPE_ADMIN_TOKEN", "")
    result = await _proxy_ragpipe("/admin/config", token=token)
    return result


# ── UI Pages ────────────────────────────────────────────────────────────────────


@app.get("/")
async def dashboard(request: Request):
    return templates.TemplateResponse(request, "dashboard.html", {"request": request})


@app.get("/collections-ui")
async def collections_page(request: Request):
    return templates.TemplateResponse(request, "collections.html", {"request": request})


@app.get("/querylog-ui")
async def querylog_page(request: Request):
    return templates.TemplateResponse(request, "querylog.html", {"request": request})


@app.get("/ingest-ui")
async def ingest_page(request: Request):
    return templates.TemplateResponse(request, "ingest.html", {"request": request})


@app.get("/metrics-ui")
async def metrics_page(request: Request):
    return templates.TemplateResponse(request, "metrics.html", {"request": request})


@app.get("/admin-ui")
async def admin_page(request: Request):
    return templates.TemplateResponse(request, "admin.html", {"request": request})
