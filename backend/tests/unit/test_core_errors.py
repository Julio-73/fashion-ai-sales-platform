"""Tests for error handling."""
from __future__ import annotations
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from app.core.errors import AppError, ErrorResponse, register_exception_handlers


class TestAppError:
    def test_default_status_code(self):
        assert AppError(code="x", message="y").status_code == 400

    def test_custom_status_code(self):
        assert AppError(code="x", message="y", status_code=404).status_code == 404

    def test_attributes(self):
        e = AppError(code="c", message="m", status_code=418)
        assert e.code == "c"
        assert e.message == "m"


class TestExceptionHandlers:
    def test_app_error_returns_correct_json(self):
        app = FastAPI()
        @app.get("/error")
        async def raise_error():
            raise AppError(code="test_error", message="Something went wrong", status_code=422)
        register_exception_handlers(app)
        client = TestClient(app)
        resp = client.get("/error")
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "test_error"

    def test_unhandled_exception_handler_logs_and_returns_500(self):
        """Test the unhandled error handler directly via app.exception_handler."""
        app = FastAPI()
        register_exception_handlers(app)

        # Use the TestClient with raise_server_exceptions=False to get the 500 response
        @app.get("/crash")
        async def crash():
            raise RuntimeError("Unexpected")

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/crash")
        assert resp.status_code == 500
        data = resp.json()
        assert data["error"]["code"] == "internal_error"


class TestErrorResponse:
    def test_model_creation(self):
        r = ErrorResponse(code="c", message="m")
        assert r.model_dump() == {"code": "c", "message": "m"}
