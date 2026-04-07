import pytest
from fastapi.testclient import TestClient

from ragdeck.main import app


@pytest.fixture()
def client():
    return TestClient(app)


class TestUIPages:
    """Regression tests for UI page endpoints.

    These tests verify that Jinja2 TemplateResponse is called with the correct
    signature (request, name, context) rather than the buggy (name, context).
    See: https://github.com/aclater/ragdeck/issues/22
    """

    @pytest.mark.parametrize(
        "path",
        [
            "/",
            "/collections-ui",
            "/querylog-ui",
            "/ingest-ui",
            "/metrics-ui",
            "/admin-ui",
        ],
    )
    def test_ui_pages_return_200_with_html(self, client, path):
        response = client.get(path)
        assert response.status_code == 200, f"{path} returned {response.status_code}"
        assert response.headers["content-type"].startswith("text/html")
        assert response.text.startswith("<!DOCTYPE html>")

    def test_dashboard_has_nav(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "ragdeck" in response.text.lower()
