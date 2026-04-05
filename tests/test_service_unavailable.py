"""Tests for graceful handling when services are unavailable."""

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


class TestServiceUnavailable:
    @patch("ragdeck.main.get_pool")
    def test_status_handles_postgres_down(self, mock_get_pool, client):
        mock_get_pool.side_effect = Exception("connection refused")

        response = client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert data["services"]["postgres"]["status"] == "down"
        assert data["status"] == "degraded"

    def test_metrics_handles_ragwatch_down(self, client):
        with patch("ragdeck.main.httpx.AsyncClient") as mock_class:
            mock_client_inst = MagicMock()
            mock_client_inst.__aenter__ = AsyncMock(side_effect=Exception("connection refused"))
            mock_client_inst.__aexit__ = AsyncMock(return_value=None)
            mock_class.return_value = mock_client_inst

            response = client.get("/metrics")
            assert response.status_code == 200
            data = response.json()
            assert "error" in data

    def test_ragpipe_metrics_handles_down(self, client):
        with patch("ragdeck.main.httpx.AsyncClient") as mock_class:
            mock_client_inst = MagicMock()
            mock_client_inst.__aenter__ = AsyncMock(side_effect=Exception("connection refused"))
            mock_client_inst.__aexit__ = AsyncMock(return_value=None)
            mock_class.return_value = mock_client_inst

            response = client.get("/metrics/ragpipe")
            assert response.status_code == 200
            data = response.json()
            assert "error" in data

    def test_collections_handles_postgres_down(self, client):
        with patch("ragdeck.main.get_pool") as mock_get_pool:
            mock_get_pool.side_effect = Exception("connection refused")

            response = client.get("/collections")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unavailable"

    def test_querylog_handles_postgres_down(self, client):
        with patch("ragdeck.main.get_pool") as mock_get_pool:
            mock_get_pool.side_effect = Exception("connection refused")

            response = client.get("/querylog")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unavailable"
