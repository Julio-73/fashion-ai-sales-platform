"""Router del módulo Admin Enterprise (Super Admin + Multi-empresa).

Todos los endpoints están bajo el prefijo ``/admin`` (registrado en
``app/api/router.py``). La protección se hace con los guardias del
módulo ``app.modules.admin.security``.
"""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status

from app.modules.admin.dependencies import (
    get_admin_audit_service,
    get_admin_auth_service,
    get_admin_service,
    get_admin_user_repository,
    get_global_metrics_service,
)
from app.modules.admin.repository import AdminUserRepository
from app.modules.admin.schemas import (
    AdminAuditListResponse,
    AdminAuthSessionResponse,
    AdminCurrentUserResponse,
    AdminLoginRequest,
    AdminLogoutRequest,
    AdminRefreshRequest,
    AdminTokenResponse,
    EmpresaAdminCreateRequest,
    EmpresaAdminListResponse,
    EmpresaAdminSummary,
    EmpresaAdminUpdateRequest,
    EmpresaStatusUpdateRequest,
    GlobalDashboardResponse,
)
from app.modules.admin.security import (
    AdminContext,
    build_admin_context_from_user,
    get_admin_context,
    require_admin_permission,
    require_super_admin,
)
from app.modules.admin.service import (
    AdminAuditService,
    AdminAuthService,
    AdminService,
    GlobalMetricsService,
)

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/auth/login", response_model=AdminAuthSessionResponse)
async def admin_login(
    payload: AdminLoginRequest,
    request: Request,
    service: Annotated[AdminAuthService, Depends(get_admin_auth_service)],
) -> AdminAuthSessionResponse:
    return await service.login(payload, ip_address=_client_ip(request))


@router.post("/auth/refresh", response_model=AdminTokenResponse)
async def admin_refresh(
    payload: AdminRefreshRequest,
    service: Annotated[AdminAuthService, Depends(get_admin_auth_service)],
) -> AdminTokenResponse:
    return await service.refresh(payload)


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def admin_logout(
    payload: AdminLogoutRequest,
    service: Annotated[AdminAuthService, Depends(get_admin_auth_service)],
) -> None:
    await service.logout(payload)


@router.get("/auth/me", response_model=AdminCurrentUserResponse)
async def admin_me(
    ctx: Annotated[AdminContext, Depends(get_admin_context)],
) -> AdminCurrentUserResponse:
    return AdminCurrentUserResponse(
        user_id=ctx.user_id,
        email=ctx.email,
        roles=ctx.roles,
        permissions=sorted(ctx.permissions),
        is_super_admin=ctx.is_super_admin,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard global
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/dashboard", response_model=GlobalDashboardResponse)
async def admin_dashboard(
    _ctx: Annotated[AdminContext, Depends(require_admin_permission("admin:dashboard:read"))],
    service: Annotated[GlobalMetricsService, Depends(get_global_metrics_service)],
) -> GlobalDashboardResponse:
    return await service.dashboard()


# ─────────────────────────────────────────────────────────────────────────────
# Empresas
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/tenants", response_model=EmpresaAdminListResponse)
async def list_tenants(
    _ctx: Annotated[AdminContext, Depends(require_admin_permission("admin:tenants:read"))],
    service: Annotated[AdminService, Depends(get_admin_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
    search: Annotated[str | None, Query(min_length=1, max_length=120)] = None,
    status: Annotated[str | None, Query(max_length=32)] = None,
    plan: Annotated[str | None, Query(max_length=32)] = None,
) -> EmpresaAdminListResponse:
    return await service.list_empresas(
        limit=limit, offset=offset, search=search, status=status, plan=plan
    )


@router.post(
    "/tenants",
    response_model=EmpresaAdminSummary,
    status_code=status.HTTP_201_CREATED,
)
async def create_tenant(
    payload: EmpresaAdminCreateRequest,
    request: Request,
    ctx: Annotated[AdminContext, Depends(require_super_admin())],
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> EmpresaAdminSummary:
    return await service.create_empresa(
        admin_user_id=ctx.user_id,
        payload=payload,
        ip_address=_client_ip(request),
    )


@router.get("/tenants/{empresa_id}", response_model=EmpresaAdminSummary)
async def get_tenant(
    empresa_id: UUID,
    _ctx: Annotated[AdminContext, Depends(require_admin_permission("admin:tenants:read"))],
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> EmpresaAdminSummary:
    return await service.get_empresa(empresa_id=empresa_id)


@router.patch("/tenants/{empresa_id}", response_model=EmpresaAdminSummary)
async def update_tenant(
    empresa_id: UUID,
    payload: EmpresaAdminUpdateRequest,
    request: Request,
    ctx: Annotated[AdminContext, Depends(require_admin_permission("admin:tenants:write"))],
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> EmpresaAdminSummary:
    return await service.update_empresa(
        admin_user_id=ctx.user_id,
        empresa_id=empresa_id,
        payload=payload,
        ip_address=_client_ip(request),
    )


@router.patch("/tenants/{empresa_id}/status", response_model=EmpresaAdminSummary)
async def update_tenant_status(
    empresa_id: UUID,
    payload: EmpresaStatusUpdateRequest,
    request: Request,
    ctx: Annotated[AdminContext, Depends(require_admin_permission("admin:tenants:write"))],
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> EmpresaAdminSummary:
    """Cambia status active / suspended / expired. Alternativa explícita a
    ``PATCH /tenants/{id}`` para acciones de suspensión / activación
    que disparan auditoría especializada (``company_suspended`` /
    ``company_activated``)."""
    return await service.update_status(
        admin_user_id=ctx.user_id,
        empresa_id=empresa_id,
        payload=payload,
        ip_address=_client_ip(request),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Audit log
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/audit", response_model=AdminAuditListResponse)
async def list_audit(
    _ctx: Annotated[AdminContext, Depends(require_admin_permission("admin:audit:read"))],
    service: Annotated[AdminAuditService, Depends(get_admin_audit_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
    action: Annotated[str | None, Query(max_length=48)] = None,
    admin_user_id: Annotated[UUID | None, Query()] = None,
    target_empresa_id: Annotated[UUID | None, Query()] = None,
) -> AdminAuditListResponse:
    return await service.list_entries(
        limit=limit,
        offset=offset,
        action=action,
        admin_user_id=admin_user_id,
        target_empresa_id=target_empresa_id,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Internal / diagnostic
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/auth/users/{user_id}", response_model=AdminCurrentUserResponse)
async def get_admin_user(
    user_id: UUID,
    _ctx: Annotated[AdminContext, Depends(require_super_admin())],
    repo: Annotated[AdminUserRepository, Depends(get_admin_user_repository)],
) -> AdminCurrentUserResponse:
    """Devuelve un admin user por id. Solo accesible por super_admin."""
    user = await repo.get_by_id(user_id=user_id)
    if user is None:
        from app.core.errors import AppError

        raise AppError(code="admin_not_found", message="Admin user not found", status_code=404)
    ctx = build_admin_context_from_user(user=user)
    return AdminCurrentUserResponse(
        user_id=ctx.user_id,
        email=ctx.email,
        roles=ctx.roles,
        permissions=sorted(ctx.permissions),
        is_super_admin=ctx.is_super_admin,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client is not None:
        return request.client.host
    return None
