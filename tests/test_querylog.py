"""Tests for /querylog endpoints."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from ragdeck.main import app


@pytest.fixture
def client():
    return TestClient(app)


class _ACM:
    def __init__(self, value):
        self._value = value
    async def __aenter__(self):
        return self._value
    async def __aexit__(self, *args):
        pass


class TestGetQuerylog:
    @patch("ragdeck.main.get_pool")
    def test_returns_entries(self, mock_get_pool, client):
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda s, k: {
            "query_hash": "abc123",
            "grounding": "corpus",
            "cited_chunks": ["doc1:0", "doc2:1"],
            "latency_ms": 120,
            "created_at": None,
        }[k]

        mock_conn = MagicMock()
        mock_conn.fetch = AsyncMock(return_value=[mock_row])
        mock_conn.fetchval = AsyncMock(return_value=1)

        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock(return_value=_ACM(mock_conn))
        mock_get_pool.return_value = mock_pool

        response = client.get("/querylog?limit=20&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        assert len(data["entries"]) == 1
        assert data["entries"][0]["grounding"] == "corpus"


class TestGetQuerylogStats:
    @patch("ragdeck.main.get_pool")
    def test_returns_stats(self, mock_get_pool, client):
        mock_row1 = MagicMock()
        mock_row1.__getitem__ = lambda s, k: {"grounding": "corpus", "count": 10, "avg_latency": 150.0}[k]
        mock_row2 = MagicMock()
        mock_row2.__getitem__ = lambda s, k: {"grounding": "general", "count": 5, "avg_latency": 80.0}[k]

        mock_conn = MagicMock()
        mock_conn.fetch = AsyncMock(return_value=[mock_row1, mock_row2])
        mock_conn.fetchval = AsyncMock(return_value=15)

        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock(return_value=_ACM(mock_conn))
        mock_get_pool.return_value = mock_pool

        response = client.get("/querylog/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 15
        assert data["by_grounding"]["corpus"]["count"] == 10
