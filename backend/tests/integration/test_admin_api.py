"""Integration tests for the Admin HTTP API.

Uses the FastAPI ``TestClient`` against the real ``app.main:app``
without touching the database — the only DB-backed endpoints are
exercised indirectly via a thin session override that returns
canned results.
"""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.security.dependencies import get_tenant_context
from app.main import app
from app.modules.admin.security import (
    ADMIN_PERMISSIONS,
    SUPER_ADMIN_ROLE,
    create_admin_access_token,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _auth_header(*, email: str = "ops@test.io", roles: list[str] | None = None) -> dict[str, str]:
    if roles is None:
        roles = [SUPER_ADMIN_ROLE]
    token = create_admin_access_token(user_id=uuid4(), email=email, roles=roles)
    return {"Authorization": f"Bearer {token}"}


class _StubScalar:
    def __init__(self, value: Any) -> None:
        self._value = value

    def scalar_one_or_none(self) -> Any:
        return self._value

    def scalars(self) -> Any:
        return _StubScalars(self._value)

    def all(self) -> list[Any]:
        if isinstance(self._value, list):
            return self._value
        return [self._value]


class _StubScalars:
    def __init__(self, value: Any) -> None:
        self._value = value

    def all(self) -> list[Any]:
        if isinstance(self._value, list):
            return self._value
        return [self._value] if self._value is not None else []


def _build_empresa() -> MagicMock:
    emp = MagicMock()
    emp.id = uuid4()
    emp.nombre = "Acme Fashion S.A."
    emp.slug = "acme-fashion"
    emp.plan = "pro"
    emp.estado = "active"
    emp.logo_url = "https://cdn.example.com/acme.png"
    emp.created_at = "2026-01-01T00:00:00Z"
    emp.updated_at = "2026-01-01T00:00:00Z"
    return emp


@pytest.fixture
def stub_session() -> MagicMock:
    session = MagicMock()
    session.add = MagicMock()
    session.add_all = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = MagicMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def admin_client(stub_session: MagicMock, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Build a TestClient that replaces the real AsyncSession with a stub.

    The admin module uses ``get_db_session`` (the same one the rest of
    the app uses) — we don't override that globally to avoid affecting
    any frozen module's test path. Instead we patch the repositories
    used by the admin service via ``monkeypatch`` so the real
    ``AsyncSession`` is bypassed.
    """
    from app.modules.admin import dependencies as admin_deps
    from app.modules.admin import service as admin_service_mod
    from app.modules.admin.repository import (
        AdminAuditRepository,
        AdminRefreshTokenRepository,
        AdminUserRepository,
        EmpresaAdminRepository,
        GlobalMetricsRepository,
    )
    from app.modules.admin.service import AdminService

    # The dashboard metrics use text() SQL which we don't need for these
    # integration tests; we focus on auth + tenants.
    monkeypatch.setattr(
        admin_deps, "get_admin_user_repository", lambda: AdminUserRepository(stub_session)
    )
    monkeypatch.setattr(
        admin_deps,
        "get_admin_refresh_repository",
        lambda: AdminRefreshTokenRepository(stub_session),
    )
    monkeypatch.setattr(
        admin_deps, "get_admin_audit_repository", lambda: AdminAuditRepository(stub_session)
    )
    monkeypatch.setattr(
        admin_deps,
        "get_empresa_admin_repository",
        lambda: EmpresaAdminRepository(stub_session),
    )
    # Avoid touching the DB for global metrics
    metrics = MagicMock(spec=GlobalMetricsRepository)
    monkeypatch.setattr(admin_deps, "get_global_metrics_repository", lambda: metrics)

    # Make sure the app does not try to use the real DB session for the
    # test client (the admin routes inject get_db_session through DI).
    # We override get_db_session to return our stub.
    from app.database.session import get_db_session

    async def _override():
        yield stub_session

    app.dependency_overrides[get_db_session] = _override

    # Ensure the original tenant dependency stays untouched
    yield TestClient(app)

    app.dependency_overrides.clear()


# ─────────────────────────────────────────────────────────────────────────────
# Auth endpoints
# ─────────────────────────────────────────────────────────────────────────────


def test_admin_login_success(admin_client: TestClient, stub_session: MagicMock) -> None:
    from app.modules.admin import service as admin_service_mod

    user = MagicMock()
    user.id = uuid4()
    user.email = "admin@test.io"
    user.password_hash = "hashed"
    user.rol = SUPER_ADMIN_ROLE
    user.is_active = True

    exec_result = MagicMock()
    exec_result.scalar_one_or_none = lambda: user
    stub_session.execute.return_value = exec_result

    original = admin_service_mod.verify_password
    admin_service_mod.verify_password = lambda _pw, _h: True
    try:
        r = admin_client.post(
            "/api/v1/admin/auth/login",
            json={"email": "admin@test.io", "password": "Admin@2024!"},
        )
    finally:
        admin_service_mod.verify_password = original
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["user"]["is_super_admin"] is True


def test_admin_login_invalid_credentials(
    admin_client: TestClient, stub_session: MagicMock
) -> None:
    user = MagicMock()
    user.password_hash = "hashed"
    exec_result = MagicMock()
    exec_result.scalar_one_or_none = lambda: user
    stub_session.execute.return_value = exec_result

    from app.modules.admin import service as admin_service_mod

    original = admin_service_mod.verify_password
    admin_service_mod.verify_password = lambda _pw, _h: False
    try:
        r = admin_client.post(
            "/api/v1/admin/auth/login",
            json={"email": "admin@test.io", "password": "bad-password"},
        )
    finally:
        admin_service_mod.verify_password = original
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "invalid_credentials"


def test_admin_login_short_password(admin_client: TestClient) -> None:
    r = admin_client.post(
        "/api/v1/admin/auth/login",
        json={"email": "admin@test.io", "password": "short"},
    )
    assert r.status_code == 422


def test_admin_me_requires_token(admin_client: TestClient) -> None:
    r = admin_client.get("/api/v1/admin/auth/me")
    assert r.status_code == 401


def test_admin_me_with_token(admin_client: TestClient) -> None:
    r = admin_client.get(
        "/api/v1/admin/auth/me", headers=_auth_header(email="me@test.io")
    )
    assert r.status_code == 200
    assert r.json()["email"] == "me@test.io"


# ─────────────────────────────────────────────────────────────────────────────
# Tenants
# ─────────────────────────────────────────────────────────────────────────────


def test_list_tenants_403_for_agent(admin_client: TestClient) -> None:
    r = admin_client.get(
        "/api/v1/admin/tenants",
        headers=_auth_header(email="agent@test.io", roles=["agent"]),
    )
    assert r.status_code == 403


def test_list_tenants_ok_for_super_admin(
    admin_client: TestClient, stub_session: MagicMock
) -> None:
    empresa = _build_empresa()
    # count + list
    stub_session.execute = AsyncMock(
        side_effect=[
            MagicMock(scalar_one=lambda: 1),  # count
            MagicMock(scalars=lambda: _StubScalars([empresa])),  # list
        ]
    )
    r = admin_client.get("/api/v1/admin/tenants", headers=_auth_header())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["slug"] == "acme-fashion"


def test_create_tenant_requires_super_admin(admin_client: TestClient) -> None:
    r = admin_client.post(
        "/api/v1/admin/tenants",
        headers=_auth_header(roles=["company_admin"]),
        json={"nombre": "New Co", "slug": "new-co", "plan": "basic"},
    )
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "super_admin_required"


def test_create_tenant_success(
    admin_client: TestClient, stub_session: MagicMock
) -> None:
    # session.add, flush, refresh
    stub_session.add = MagicMock()
    stub_session.flush = AsyncMock()

    async def _fake_refresh(obj):
        from datetime import UTC, datetime as _dt

        if getattr(obj, "created_at", None) is None:
            obj.created_at = _dt.now(UTC)
        if getattr(obj, "updated_at", None) is None:
            obj.updated_at = _dt.now(UTC)

    stub_session.refresh = AsyncMock(side_effect=_fake_refresh)
    r = admin_client.post(
        "/api/v1/admin/tenants",
        headers=_auth_header(),
        json={"nombre": "New Co", "slug": "new-co", "plan": "pro", "status": "active"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["slug"] == "new-co"
    assert body["plan"] == "pro"


def test_create_tenant_rejects_invalid_plan(admin_client: TestClient) -> None:
    r = admin_client.post(
        "/api/v1/admin/tenants",
        headers=_auth_header(),
        json={"nombre": "New Co", "slug": "new-co", "plan": "nope"},
    )
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_plan"


def test_update_tenant_status_suspended(
    admin_client: TestClient, stub_session: MagicMock
) -> None:
    empresa = _build_empresa()
    empresa.estado = "suspended"
    stub_session.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=lambda: empresa)
    )
    stub_session.flush = AsyncMock()
    stub_session.refresh = AsyncMock()

    r = admin_client.patch(
        f"/api/v1/admin/tenants/{empresa.id}/status",
        headers=_auth_header(),
        json={"status": "suspended"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "suspended"


def test_get_tenant_404(admin_client: TestClient, stub_session: MagicMock) -> None:
    stub_session.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=lambda: None)
    )
    r = admin_client.get(
        f"/api/v1/admin/tenants/{uuid4()}", headers=_auth_header()
    )
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "empresa_not_found"


# ─────────────────────────────────────────────────────────────────────────────
# Audit
# ─────────────────────────────────────────────────────────────────────────────


def test_list_audit(admin_client: TestClient, stub_session: MagicMock) -> None:
    entry = MagicMock()
    entry.id = uuid4()
    entry.admin_user_id = uuid4()
    entry.target_empresa_id = None
    entry.action = "company_suspended"
    entry.details = None
    entry.ip_address = "127.0.0.1"
    entry.created_at = "2026-06-01T00:00:00Z"
    entry.admin_email = "ops@test.io"

    stub_session.execute = AsyncMock(
        side_effect=[
            MagicMock(scalar_one=lambda: 1),
            MagicMock(scalars=lambda: _StubScalars([entry])),
        ]
    )
    r = admin_client.get("/api/v1/admin/audit", headers=_auth_header())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["action"] == "company_suspended"


# ─────────────────────────────────────────────────────────────────────────────
# Health check still works
# ─────────────────────────────────────────────────────────────────────────────


def test_health_endpoint_still_works(admin_client: TestClient) -> None:
    r = admin_client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
