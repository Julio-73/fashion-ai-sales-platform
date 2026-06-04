"""Fixtures compartidos para los tests del módulo Admin."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from app.core.security.dependencies import AuthenticatedUser
from app.modules.admin.models import SUPER_ADMIN_ROLE, AdminUser
from app.modules.admin.repository import (
    AdminAuditRepository,
    AdminRefreshTokenRepository,
    AdminUserRepository,
    EmpresaAdminRepository,
    GlobalMetricsRepository,
)
from app.modules.admin.security import AdminContext, ADMIN_PERMISSIONS
from app.modules.admin.service import (
    AdminAuditService,
    AdminAuthService,
    AdminService,
    GlobalMetricsService,
)
from app.modules.companies.models import Empresa

TEST_ADMIN_USER_ID = UUID("aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee")
TEST_TARGET_EMPRESA_ID = UUID("99999999-9999-4999-8999-999999999999")


def _permissions_for(roles: list[str]) -> set[str]:
    perms: set[str] = set()
    for r in roles:
        perms.update(ADMIN_PERMISSIONS.get(r, set()))
    return perms


@pytest.fixture
def admin_user() -> AdminUser:
    user = MagicMock(spec=AdminUser)
    user.id = TEST_ADMIN_USER_ID
    user.email = "admin@test.io"
    user.full_name = "Test Super Admin"
    user.rol = SUPER_ADMIN_ROLE
    user.is_active = True
    user.password_hash = "hashed:Admin@2024!"
    return user


@pytest.fixture
def admin_context() -> AdminContext:
    roles = [SUPER_ADMIN_ROLE]
    return AdminContext(
        user_id=TEST_ADMIN_USER_ID,
        email="admin@test.io",
        roles=roles,
        permissions=_permissions_for(roles),
        is_super_admin=True,
    )


@pytest.fixture
def admin_user_repo(mock_session: AsyncMock) -> AdminUserRepository:
    return AdminUserRepository(session=mock_session)


@pytest.fixture
def admin_refresh_repo(mock_session: AsyncMock) -> AdminRefreshTokenRepository:
    return AdminRefreshTokenRepository(session=mock_session)


@pytest.fixture
def admin_audit_repo(mock_session: AsyncMock) -> AdminAuditRepository:
    return AdminAuditRepository(session=mock_session)


@pytest.fixture
def empresa_admin_repo(mock_session: AsyncMock) -> EmpresaAdminRepository:
    return EmpresaAdminRepository(session=mock_session)


@pytest.fixture
def global_metrics_repo(mock_session: AsyncMock) -> GlobalMetricsRepository:
    return GlobalMetricsRepository(session=mock_session)


@pytest.fixture
def admin_auth_service(
    admin_user_repo: AdminUserRepository,
    admin_refresh_repo: AdminRefreshTokenRepository,
    admin_audit_repo: AdminAuditRepository,
) -> AdminAuthService:
    return AdminAuthService(
        user_repo=admin_user_repo, refresh_repo=admin_refresh_repo, audit_repo=admin_audit_repo
    )


@pytest.fixture
def admin_service(
    empresa_admin_repo: EmpresaAdminRepository,
    admin_audit_repo: AdminAuditRepository,
    admin_user_repo: AdminUserRepository,
) -> AdminService:
    return AdminService(
        empresas_repo=empresa_admin_repo, audit_repo=admin_audit_repo, user_repo=admin_user_repo
    )


@pytest.fixture
def admin_audit_service(
    admin_audit_repo: AdminAuditRepository,
) -> AdminAuditService:
    return AdminAuditService(repo=admin_audit_repo)


@pytest.fixture
def global_metrics_service(
    empresa_admin_repo: EmpresaAdminRepository,
    global_metrics_repo: GlobalMetricsRepository,
) -> GlobalMetricsService:
    return GlobalMetricsService(empresas_repo=empresa_admin_repo, metrics_repo=global_metrics_repo)


@pytest.fixture
def sample_empresa() -> Empresa:
    emp = MagicMock(spec=Empresa)
    emp.id = TEST_TARGET_EMPRESA_ID
    emp.nombre = "Acme Fashion S.A."
    emp.slug = "acme-fashion"
    emp.plan = "pro"
    emp.estado = "active"
    emp.logo_url = "https://cdn.example.com/acme.png"
    emp.created_at = "2026-01-01T00:00:00Z"
    emp.updated_at = "2026-01-01T00:00:00Z"
    return emp


# Re-use the parent mock_session fixture defined in tests/conftest.py
_ = AuthenticatedUser  # silence unused import warnings
