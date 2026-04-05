"""Tests for GET /health."""
import pytest
from fastapi.testclient import TestClient

from ragdeck.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.json() == {"status": "ok"}
