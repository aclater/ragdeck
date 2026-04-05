"""Tests for auth on POST/DELETE endpoints."""

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


class TestAuthRequired:
    def test_trigger_ingest_requires_auth(self, client):
        response = client.post("/ingest/trigger")
        assert response.status_code == 401

    def test_trigger_ingest_full_requires_auth(self, client):
        response = client.post("/ingest/trigger-full")
        assert response.status_code == 401

    def test_delete_collection_requires_auth(self, client):
        response = client.delete("/collections/test")
        assert response.status_code == 401

    def test_reload_routes_requires_auth(self, client):
        response = client.post("/admin/reload-routes", json={})
        assert response.status_code == 401

    def test_reload_prompt_requires_auth(self, client):
        response = client.post("/admin/reload-prompt", json={})
        assert response.status_code == 401

    def test_run_probe_requires_auth(self, client):
        response = client.post("/probe/run")
        assert response.status_code == 401

    def test_wrong_token_rejected(self, client):
        with patch.dict("ragdeck.main.__dict__", {"ADMIN_TOKEN": "correct-token"}):
            response = client.post(
                "/ingest/trigger",
                headers={"Authorization": "Bearer wrong-token"},
            )
            assert response.status_code == 401

    def test_bearer_token_accepted(self, client):
        with patch.dict(
            "ragdeck.main.__dict__",
            {
                "ADMIN_TOKEN": "correct-token",
                "RAGSTUFFER_ADMIN_TOKEN": "stuffer-token",
            },
        ):
            with patch("ragdeck.main.httpx.AsyncClient") as mock_class:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.json = lambda: {"status": "triggered", "mode": "incremental"}

                mock_client_inst = MagicMock()
                mock_client_inst.__aenter__ = AsyncMock(return_value=mock_client_inst)
                mock_client_inst.__aexit__ = AsyncMock(return_value=None)
                mock_client_inst.post = AsyncMock(return_value=mock_resp)
                mock_class.return_value = mock_client_inst

                response = client.post(
                    "/ingest/trigger",
                    headers={"Authorization": "Bearer correct-token"},
                )
                assert response.status_code == 200
