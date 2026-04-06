import pytest
from fastapi.testclient import TestClient

from ragdeck.main import app


@pytest.fixture()
def client():
    return TestClient(app)


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_status_includes_ragorchestrator(client):
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert "services" in data
    assert "ragorchestrator" in data["services"]
