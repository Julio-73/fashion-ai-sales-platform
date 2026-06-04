"""Wiring de dependencias (DI) del módulo Admin."""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.modules.admin.repository import (
    AdminAuditRepository,
    AdminRefreshTokenRepository,
    AdminUserRepository,
    EmpresaAdminRepository,
    GlobalMetricsRepository,
)
from app.modules.admin.service import (
    AdminAuditService,
    AdminAuthService,
    AdminService,
    GlobalMetricsService,
)


async def get_admin_user_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AdminUserRepository:
    return AdminUserRepository(session=session)


async def get_admin_refresh_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AdminRefreshTokenRepository:
    return AdminRefreshTokenRepository(session=session)


async def get_admin_audit_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AdminAuditRepository:
    return AdminAuditRepository(session=session)


async def get_empresa_admin_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> EmpresaAdminRepository:
    return EmpresaAdminRepository(session=session)


async def get_global_metrics_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> GlobalMetricsRepository:
    return GlobalMetricsRepository(session=session)


async def get_admin_auth_service(
    users: Annotated[AdminUserRepository, Depends(get_admin_user_repository)],
    refresh: Annotated[AdminRefreshTokenRepository, Depends(get_admin_refresh_repository)],
    audit: Annotated[AdminAuditRepository, Depends(get_admin_audit_repository)],
) -> AdminAuthService:
    return AdminAuthService(user_repo=users, refresh_repo=refresh, audit_repo=audit)


async def get_admin_service(
    empresas: Annotated[EmpresaAdminRepository, Depends(get_empresa_admin_repository)],
    audit: Annotated[AdminAuditRepository, Depends(get_admin_audit_repository)],
    users: Annotated[AdminUserRepository, Depends(get_admin_user_repository)],
) -> AdminService:
    return AdminService(empresas_repo=empresas, audit_repo=audit, user_repo=users)


async def get_admin_audit_service(
    repo: Annotated[AdminAuditRepository, Depends(get_admin_audit_repository)],
) -> AdminAuditService:
    return AdminAuditService(repo=repo)


async def get_global_metrics_service(
    empresas: Annotated[EmpresaAdminRepository, Depends(get_empresa_admin_repository)],
    metrics: Annotated[GlobalMetricsRepository, Depends(get_global_metrics_repository)],
) -> GlobalMetricsService:
    return GlobalMetricsService(empresas_repo=empresas, metrics_repo=metrics)
