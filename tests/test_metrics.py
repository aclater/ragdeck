"""Tests for /metrics endpoints."""
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


class TestMetricsEndpoint:
    def test_proxies_ragwatch_summary(self, client):
        with patch("ragdeck.main.httpx.AsyncClient") as mock_class:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json = lambda: {"status": "up", "sources": {}}

            mock_client_inst = MagicMock()
            mock_client_inst.__aenter__ = AsyncMock(return_value=mock_client_inst)
            mock_client_inst.__aexit__ = AsyncMock(return_value=None)
            mock_client_inst.get = AsyncMock(return_value=mock_resp)
            mock_class.return_value = mock_client_inst

            response = client.get("/metrics")
            assert response.status_code == 200


class TestMetricsRagpipe:
    def test_proxies_ragpipe_metrics(self, client):
        with patch("ragdeck.main.httpx.AsyncClient") as mock_class:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.text = "ragpipe_queries_total 42\n"

            mock_client_inst = MagicMock()
            mock_client_inst.__aenter__ = AsyncMock(return_value=mock_client_inst)
            mock_client_inst.__aexit__ = AsyncMock(return_value=None)
            mock_client_inst.get = AsyncMock(return_value=mock_resp)
            mock_class.return_value = mock_client_inst

            response = client.get("/metrics/ragpipe")
            assert response.status_code == 200
            data = response.json()
            assert "metrics" in data


class TestMetricsRagstuffer:
    def test_proxies_ragstuffer_metrics(self, client):
        with patch("ragdeck.main.httpx.AsyncClient") as mock_class:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.text = "ragstuffer_documents_ingested_total 5\n"

            mock_client_inst = MagicMock()
            mock_client_inst.__aenter__ = AsyncMock(return_value=mock_client_inst)
            mock_client_inst.__aexit__ = AsyncMock(return_value=None)
            mock_client_inst.get = AsyncMock(return_value=mock_resp)
            mock_class.return_value = mock_client_inst

            response = client.get("/metrics/ragstuffer")
            assert response.status_code == 200
            data = response.json()
            assert "metrics" in data
