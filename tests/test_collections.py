"""Tests for /collections endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from ragdeck.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestListCollections:
    @patch("ragdeck.main.get_pool")
    def test_returns_collections_list(self, mock_get_pool, client):
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda s, k: {
            "id": "abc",
            "name": "test-col",
            "description": "",
            "source_types": '["drive"]',
            "created_at": None,
        }[k]

        mock_conn = MagicMock()
        mock_conn.fetch = AsyncMock(return_value=[mock_row])

        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock(return_value=_ACM(mock_conn))
        mock_get_pool.return_value = mock_pool

        with patch("ragdeck.main.QDRANT_URL", "http://localhost:6333"):
            with patch("ragdeck.main.httpx.AsyncClient") as mock_http:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.json = lambda: {"result": {"collections": []}}
                mock_http.return_value.__aenter__ = AsyncMock(return_value=mock_http.return_value)
                mock_http.return_value.__aexit__ = AsyncMock(return_value=None)
                mock_http.return_value.get = AsyncMock(return_value=mock_resp)

                response = client.get("/collections")
                assert response.status_code == 200
                data = response.json()
                assert "collections" in data
                assert len(data["collections"]) == 1
                assert data["collections"][0]["name"] == "test-col"


class TestDeleteCollection:
    def test_rejects_missing_token(self, client):
        response = client.delete("/collections/test-col")
        assert response.status_code == 401

    def test_rejects_wrong_token(self, client):
        with patch.dict("ragdeck.main.__dict__", {"ADMIN_TOKEN": "correct"}):
            response = client.delete(
                "/collections/test-col",
                headers={"Authorization": "Bearer wrong"},
            )
            assert response.status_code == 401


class _ACM:
    """Async context manager wrapper for a sync mock."""

    def __init__(self, value):
        self._value = value

    async def __aenter__(self):
        return self._value

    async def __aexit__(self, *args):
        pass
