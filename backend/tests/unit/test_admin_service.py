"""Unit tests for the Admin service layer (auth + tenant + audit + metrics)."""
from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from app.core.errors import AppError
from app.modules.admin.models import (
    DEFAULT_EMPRESA_PLAN,
    DEFAULT_EMPRESA_STATUS,
    SUPER_ADMIN_ROLE,
    AdminUser,
)
from app.modules.admin.schemas import (
    AdminLoginRequest,
    AdminLogoutRequest,
    AdminRefreshRequest,
    EmpresaAdminCreateRequest,
    EmpresaAdminUpdateRequest,
    EmpresaStatusUpdateRequest,
)
from app.modules.admin.security import (
    AdminContext,
    ADMIN_PERMISSIONS,
    create_admin_access_token,
    create_admin_refresh_token,
    hash_admin_refresh_token,
    verify_admin_access_token,
)
from app.modules.admin.service import (
    AdminAuditService,
    AdminAuthService,
    AdminService,
    EMPRESA_PLANS,
    EMPRESA_STATUS,
    GlobalMetricsService,
)


# ─────────────────────────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_admin_login_success(
    admin_auth_service: AdminAuthService, admin_user: MagicMock
) -> None:
    admin_user_repo = admin_auth_service._users
    admin_user_repo.get_by_email = AsyncMock(return_value=admin_user)
    admin_user_repo.update_last_login = AsyncMock()
    refresh_repo = admin_auth_service._refresh
    refresh_repo.create = AsyncMock()
    refresh_repo.commit = AsyncMock()
    audit_repo = admin_auth_service._audit
    audit_repo.record = AsyncMock()
    audit_repo.commit = AsyncMock()

    # The service imports verify_password as a name at module load, so we
    # must patch the name actually referenced inside the service module.
    from app.modules.admin import service as admin_service_mod

    original_verify = admin_service_mod.verify_password
    admin_service_mod.verify_password = lambda _pw, _h: True
    try:
        resp = await admin_auth_service.login(
            AdminLoginRequest(email="admin@test.io", password="whatever-password")
        )
    finally:
        admin_service_mod.verify_password = original_verify

    assert resp.access_token
    assert resp.refresh_token
    assert resp.user.email == "admin@test.io"
    assert resp.user.is_super_admin is True
    # Token must be verifiable as admin
    payload = verify_admin_access_token(resp.access_token)
    assert payload.typ == "admin_access"


@pytest.mark.asyncio
async def test_admin_login_wrong_password(
    admin_auth_service: AdminAuthService, admin_user: MagicMock
) -> None:
    admin_auth_service._users.get_by_email = AsyncMock(return_value=admin_user)
    from app.modules.admin import service as admin_service_mod

    original_verify = admin_service_mod.verify_password
    admin_service_mod.verify_password = lambda _pw, _h: False
    try:
        with pytest.raises(AppError) as exc:
            await admin_auth_service.login(
                AdminLoginRequest(email="admin@test.io", password="bad-password")
            )
    finally:
        admin_service_mod.verify_password = original_verify
    assert exc.value.status_code == 401
    assert exc.value.code == "invalid_credentials"


@pytest.mark.asyncio
async def test_admin_login_inactive_account(
    admin_auth_service: AdminAuthService, admin_user: MagicMock
) -> None:
    admin_user.is_active = False
    admin_auth_service._users.get_by_email = AsyncMock(return_value=admin_user)
    from app.modules.admin import service as admin_service_mod

    original_verify = admin_service_mod.verify_password
    admin_service_mod.verify_password = lambda _pw, _h: True
    try:
        with pytest.raises(AppError) as exc:
            await admin_auth_service.login(
                AdminLoginRequest(email="admin@test.io", password="whatever-password")
            )
    finally:
        admin_service_mod.verify_password = original_verify
    assert exc.value.status_code == 403
    assert exc.value.code == "account_disabled"


@pytest.mark.asyncio
async def test_admin_refresh_reuses_active_token(
    admin_auth_service: AdminAuthService, admin_user: MagicMock
) -> None:
    user_id = uuid4()
    admin_user.id = user_id
    admin_user.rol = SUPER_ADMIN_ROLE
    admin_user.is_active = True
    refresh_record = MagicMock()
    refresh_record.admin_user_id = user_id
    refresh_record.family_id = uuid4()

    admin_auth_service._refresh.get_active = AsyncMock(return_value=refresh_record)
    admin_auth_service._refresh.get_by_hash = AsyncMock(return_value=None)
    admin_auth_service._refresh.create = AsyncMock(return_value=MagicMock(id=uuid4()))
    admin_auth_service._refresh.revoke = AsyncMock()
    admin_auth_service._refresh.commit = AsyncMock()
    admin_auth_service._users.get_by_id = AsyncMock(return_value=admin_user)

    token, token_hash, family_id, expires_at = create_admin_refresh_token()
    payload = AdminRefreshRequest(refresh_token=token)
    resp = await admin_auth_service.refresh(payload)
    assert resp.access_token
    # Verify it is an admin token
    decoded = verify_admin_access_token(resp.access_token)
    assert decoded.sub == user_id
    _ = (token_hash, family_id, expires_at)


@pytest.mark.asyncio
async def test_admin_refresh_rejects_stale_token(
    admin_auth_service: AdminAuthService,
) -> None:
    admin_auth_service._refresh.get_active = AsyncMock(return_value=None)
    admin_auth_service._refresh.get_by_hash = AsyncMock(return_value=None)
    admin_auth_service._refresh.revoke_family = AsyncMock()
    admin_auth_service._refresh.commit = AsyncMock()

    token, *_ = create_admin_refresh_token()
    with pytest.raises(AppError) as exc:
        await admin_auth_service.refresh(AdminRefreshRequest(refresh_token=token))
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_admin_logout_revokes_active_token(
    admin_auth_service: AdminAuthService,
) -> None:
    record = MagicMock()
    record.revoked_at = None
    admin_auth_service._refresh.get_by_hash = AsyncMock(return_value=record)
    admin_auth_service._refresh.revoke = AsyncMock()
    admin_auth_service._refresh.commit = AsyncMock()

    token, *_ = create_admin_refresh_token()
    await admin_auth_service.logout(AdminLogoutRequest(refresh_token=token))
    admin_auth_service._refresh.revoke.assert_awaited_once()


# ─────────────────────────────────────────────────────────────────────────────
# Tenant management
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_empresa_rejects_invalid_plan(
    admin_service: AdminService,
) -> None:
    with pytest.raises(AppError) as exc:
        await admin_service.create_empresa(
            admin_user_id=uuid4(),
            payload=EmpresaAdminCreateRequest(
                nombre="Acme Test", slug="x-corp", plan="unknown"
            ),
        )
    assert exc.value.status_code == 400
    assert exc.value.code == "invalid_plan"


@pytest.mark.asyncio
async def test_create_empresa_rejects_invalid_status(
    admin_service: AdminService,
) -> None:
    with pytest.raises(AppError) as exc:
        await admin_service.create_empresa(
            admin_user_id=uuid4(),
            payload=EmpresaAdminCreateRequest(
                nombre="Acme Test", slug="x-corp", plan="basic", status="garbage"
            ),
        )
    assert exc.value.status_code == 400
    assert exc.value.code == "invalid_status"


@pytest.mark.asyncio
async def test_create_empresa_success_records_audit(
    admin_service: AdminService, sample_empresa: MagicMock
) -> None:
    session = admin_service._empresas._session
    session.add = MagicMock()
    session.flush = AsyncMock()

    async def _fake_refresh(obj):
        # Simulate DB-side defaults so the summary schema can validate.
        from datetime import UTC, datetime as _dt

        if getattr(obj, "created_at", None) is None:
            obj.created_at = _dt.now(UTC)
        if getattr(obj, "updated_at", None) is None:
            obj.updated_at = _dt.now(UTC)

    session.refresh = AsyncMock(side_effect=_fake_refresh)
    admin_service._empresas.commit = AsyncMock()
    admin_service._audit.record = AsyncMock()

    payload = EmpresaAdminCreateRequest(
        nombre="Acme Fashion S.A.", slug="acme-fashion", plan="pro", status="active"
    )
    summary = await admin_service.create_empresa(
        admin_user_id=uuid4(), payload=payload, ip_address="127.0.0.1"
    )
    assert summary.slug == "acme-fashion"
    assert summary.plan == "pro"
    assert summary.status == "active"
    assert summary.created_at is not None
    assert summary.updated_at is not None
    admin_service._audit.record.assert_awaited_once()
    args, kwargs = admin_service._audit.record.call_args
    assert kwargs["action"] == "company_created"


@pytest.mark.asyncio
async def test_update_empresa_status_to_suspended(
    admin_service: AdminService, sample_empresa: MagicMock
) -> None:
    admin_service._empresas.get_by_id = AsyncMock(return_value=sample_empresa)
    admin_service._empresas.update_status = AsyncMock()
    sample_empresa.estado = "suspended"  # what update_status does
    admin_service._empresas._session.refresh = AsyncMock()
    admin_service._empresas.commit = AsyncMock()
    admin_service._audit.record = AsyncMock()

    summary = await admin_service.update_status(
        admin_user_id=uuid4(),
        empresa_id=sample_empresa.id,
        payload=EmpresaStatusUpdateRequest(status="suspended"),
        ip_address="10.0.0.1",
    )
    assert summary.status == "suspended"
    args, kwargs = admin_service._audit.record.call_args
    assert kwargs["action"] == "company_suspended"
    assert kwargs["target_empresa_id"] == sample_empresa.id


@pytest.mark.asyncio
async def test_update_empresa_404(admin_service: AdminService) -> None:
    admin_service._empresas.get_by_id = AsyncMock(return_value=None)
    with pytest.raises(AppError) as exc:
        await admin_service.update_empresa(
            admin_user_id=uuid4(),
            empresa_id=uuid4(),
            payload=EmpresaAdminUpdateRequest(nombre="New name"),
        )
    assert exc.value.status_code == 404
    assert exc.value.code == "empresa_not_found"


@pytest.mark.asyncio
async def test_list_empresas(
    admin_service: AdminService, sample_empresa: MagicMock
) -> None:
    admin_service._empresas.list_all = AsyncMock(return_value=([sample_empresa], 1))
    response = await admin_service.list_empresas(
        limit=10, offset=0, search=None, status=None, plan=None
    )
    assert response.total == 1
    assert response.items[0].slug == "acme-fashion"


# ─────────────────────────────────────────────────────────────────────────────
# Audit
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_audit_record_validates_action(
    admin_audit_repo: MagicMock,
) -> None:
    with pytest.raises(ValueError):
        await admin_audit_repo.record(
            admin_user_id=uuid4(),
            action="not_a_real_action",
        )


@pytest.mark.asyncio
async def test_audit_list(admin_audit_service: AdminAuditService) -> None:
    entry = MagicMock()
    entry.id = uuid4()
    entry.admin_user_id = uuid4()
    entry.target_empresa_id = None
    entry.action = "company_created"
    entry.details = None
    entry.ip_address = "127.0.0.1"
    entry.created_at = datetime.now(UTC)
    # The service projects ``admin_email`` via the response schema; it is
    # not on the model directly, so we need to give the mock a real value
    # for ``model_validate`` to consume.
    entry.admin_email = "ops@test.io"
    admin_audit_service._repo.list = AsyncMock(return_value=([entry], 1))
    response = await admin_audit_service.list_entries(
        limit=10, offset=0, action=None, admin_user_id=None, target_empresa_id=None
    )
    assert response.total == 1
    assert response.items[0].action == "company_created"
    assert response.items[0].admin_email == "ops@test.io"


# ─────────────────────────────────────────────────────────────────────────────
# Global metrics
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_global_dashboard_aggregates(
    global_metrics_service: GlobalMetricsService,
) -> None:
    global_metrics_service._empresas.count_by_status = AsyncMock(
        return_value={"active": 5, "suspended": 2, "expired": 1}
    )
    global_metrics_service._empresas.count_by_plan = AsyncMock(
        return_value={"basic": 4, "pro": 3, "enterprise": 1}
    )
    global_metrics_service._metrics.total_clientes = AsyncMock(return_value=120)
    global_metrics_service._metrics.total_pedidos = AsyncMock(return_value=42)
    global_metrics_service._metrics.total_conversaciones = AsyncMock(return_value=87)
    global_metrics_service._metrics.total_ventas = AsyncMock(return_value=12345.67)

    dash = await global_metrics_service.dashboard()
    assert dash.total_empresas == 8
    assert dash.empresas_activas == 5
    assert dash.empresas_suspendidas == 2
    assert dash.empresas_expiradas == 1
    assert dash.total_clientes == 120
    assert dash.total_pedidos == 42
    assert dash.total_conversaciones == 87
    assert dash.total_ventas == 12345.67
    assert dash.planes_breakdown == {"basic": 4, "pro": 3, "enterprise": 1}
    assert dash.status_breakdown == {"active": 5, "suspended": 2, "expired": 1}


# ─────────────────────────────────────────────────────────────────────────────
# Constants / schemas
# ─────────────────────────────────────────────────────────────────────────────


def test_constants_are_complete() -> None:
    assert set(EMPRESA_STATUS) == {"active", "suspended", "expired"}
    assert set(EMPRESA_PLANS) == {"basic", "pro", "enterprise"}


def test_default_empresa_values() -> None:
    assert DEFAULT_EMPRESA_PLAN == "basic"
    assert DEFAULT_EMPRESA_STATUS == "active"
