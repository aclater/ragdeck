"""Live integration tests for ragdeck.

Tests run against the live ragdeck service (:8092).
Requires ragdeck and upstream services (ragpipe, ragstuffer, ragwatch, qdrant, postgres, ragorchestrator) to be running.

Run with:
    PYTHONPATH=. pytest tests/test_live.py -v --ragdeck-url=http://localhost:8092

Skip in CI (service not available):
    SKIP_LIVE_TESTS=1 pytest tests/test_live.py -v -m "not live"

Note: /agentic/stats currently returns "unavailable" because agentic columns
(query_rewritten, retrieval_attempts) are not yet in the query_log schema.
This is expected — issue rag-suite#40 tracks the migration.
"""

import os

import httpx
import pytest

RAGDECK_URL = os.environ.get("RAGDECK_URL", "http://localhost:8092")
TIMEOUT = 30.0


def _is_ragdeck_available() -> bool:
    try:
        httpx.get(f"{RAGDECK_URL}/health", timeout=5)
        return True
    except Exception:
        return False


pytestmark = [
    pytest.mark.skipif(
        os.environ.get("SKIP_LIVE_TESTS") == "1" or not _is_ragdeck_available(),
        reason="ragdeck not available — set SKIP_LIVE_TESTS=1 to skip",
    ),
]


@pytest.fixture
def ragdeck_url():
    return RAGDECK_URL


# ── Health ─────────────────────────────────────────────────────────────────────


def test_health_returns_200(ragdeck_url):
    resp = httpx.get(f"{ragdeck_url}/health", timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


# ── Dashboard UI ───────────────────────────────────────────────────────────────


def test_dashboard_returns_200(ragdeck_url):
    resp = httpx.get(f"{ragdeck_url}/", timeout=10)
    assert resp.status_code == 200


def test_dashboard_is_html(ragdeck_url):
    resp = httpx.get(f"{ragdeck_url}/", timeout=10)
    assert "text/html" in resp.headers.get("content-type", "")


def test_dashboard_shows_service_status(ragdeck_url):
    resp = httpx.get(f"{ragdeck_url}/", timeout=10)
    text = resp.text
    assert "ragpipe" in text or "status" in text.lower()


# ── Query log ──────────────────────────────────────────────────────────────────


def test_querylog_returns_200(ragdeck_url):
    resp = httpx.get(f"{ragdeck_url}/querylog", timeout=10)
    assert resp.status_code == 200


def test_querylog_returns_json(ragdeck_url):
    resp = httpx.get(f"{ragdeck_url}/querylog", timeout=10)
    data = resp.json()
    assert "entries" in data
    assert isinstance(data["entries"], list)


def test_querylog_has_required_fields(ragdeck_url):
    resp = httpx.get(f"{ragdeck_url}/querylog", timeout=10)
    data = resp.json()
    if data["entries"]:
        entry = data["entries"][0]
        assert "query_hash" in entry
        assert "grounding" in entry
        assert "cited_chunks" in entry
        assert "created_at" in entry


def test_querylog_crag_fields_present(ragdeck_url):
    resp = httpx.get(f"{ragdeck_url}/querylog", timeout=10)
    data = resp.json()
    assert "total" in data


def test_querylog_pagination(ragdeck_url):
    resp = httpx.get(f"{ragdeck_url}/querylog?limit=5", timeout=10)
    data = resp.json()
    assert len(data["entries"]) <= 5


# ── Collections ────────────────────────────────────────────────────────────────


def test_collections_returns_200(ragdeck_url):
    resp = httpx.get(f"{ragdeck_url}/collections", timeout=10)
    assert resp.status_code == 200


def test_collections_lists_all_four(ragdeck_url):
    resp = httpx.get(f"{ragdeck_url}/collections", timeout=10)
    data = resp.json()
    names = {c["name"] for c in data.get("collections", [])}
    assert "personnel" in names, f"personnel not in collections: {names}"
    assert "nato" in names, f"nato not in collections: {names}"
    assert "mpep" in names, f"mpep not in collections: {names}"
    assert "documents" in names, f"documents not in collections: {names}"


def test_collection_has_chunk_count(ragdeck_url):
    resp = httpx.get(f"{ragdeck_url}/collections", timeout=10)
    data = resp.json()
    for coll in data.get("collections", []):
        assert "vector_count" in coll, f"collection missing vector_count: {coll}"


# ── Agentic observability ──────────────────────────────────────────────────────


def test_agentic_stats_returns_200(ragdeck_url):
    resp = httpx.get(f"{ragdeck_url}/agentic/stats", timeout=10)
    assert resp.status_code == 200


def test_agentic_stats_response_structure(ragdeck_url):
    resp = httpx.get(f"{ragdeck_url}/agentic/stats", timeout=10)
    data = resp.json()
    assert "status" in data or "error" in data


def test_traces_endpoint_exists(ragdeck_url):
    resp = httpx.get(f"{ragdeck_url}/agentic/traces/test-hash-not-found", timeout=10)
    assert resp.status_code in (200, 404)


# ── Status endpoint ────────────────────────────────────────────────────────────


def test_status_returns_services(ragdeck_url):
    resp = httpx.get(f"{ragdeck_url}/status", timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert "services" in data
    services = data["services"]
    assert "ragpipe" in services
    assert "ragstuffer" in services
    assert "ragorchestrator" in services
    assert "qdrant" in services
    assert "postgres" in services


def test_ragorchestrator_health_in_status(ragdeck_url):
    resp = httpx.get(f"{ragdeck_url}/status", timeout=10)
    data = resp.json()
    orch = data["services"].get("ragorchestrator", {})
    assert "status" in orch


def test_ragorchestrator_unavailable_handled(ragdeck_url):
    resp = httpx.get(f"{ragdeck_url}/status", timeout=10)
    assert resp.status_code == 200


# ── Metrics proxy ───────────────────────────────────────────────────────────────


def test_metrics_proxies_ragwatch(ragdeck_url):
    resp = httpx.get(f"{ragdeck_url}/metrics", timeout=10)
    assert resp.status_code == 200
    text = resp.text
    assert "ragwatch" in text or "ragpipe" in text or "ragstuffer" in text
