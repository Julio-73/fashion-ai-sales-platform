"""Integration tests for API endpoints."""
from __future__ import annotations
import pytest
from fastapi.testclient import TestClient
from app.main import create_app


@pytest.fixture(scope="module")
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self, client: TestClient):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "ai-sales-agent-saas-api"

    def test_health_content_type(self, client: TestClient):
        resp = client.get("/api/v1/health")
        assert resp.headers["content-type"] == "application/json"


class TestSecurityHeaders:
    def test_security_headers_present(self, client: TestClient):
        resp = client.get("/api/v1/health")
        assert "x-request-id" in resp.headers
        assert resp.headers["x-content-type-options"] == "nosniff"
        assert resp.headers["referrer-policy"] == "strict-origin-when-cross-origin"
