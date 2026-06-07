"""Services del módulo Admin Enterprise.

- ``AdminAuthService``: login / refresh / logout de AdminUsers.
- ``AdminService``: gestión de empresas (CRUD, suspender, activar, plan).
- ``AdminAuditService``: registro y consulta de auditoría.
- ``GlobalMetricsService``: agregaciones cross-tenant.
"""
from __future__ import annotations

import logging
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security.password import verify_password
from app.modules.admin.models import (
    DEFAULT_EMPRESA_PLAN,
    DEFAULT_EMPRESA_STATUS,
    EMPRESA_PLANS,
    EMPRESA_STATUS,
    SUPER_ADMIN_ROLE,
)
from app.modules.admin.repository import (
    AdminAuditRepository,
    AdminRefreshTokenRepository,
    AdminUserRepository,
    EmpresaAdminRepository,
    GlobalMetricsRepository,
)
from app.modules.admin.schemas import (
    AdminAuthSessionResponse,
    AdminAuditEntryResponse,
    AdminAuditListResponse,
    AdminCurrentUserResponse,
    AdminLoginRequest,
    AdminLogoutRequest,
    AdminRefreshRequest,
    AdminTokenResponse,
    EMPRESA_PLAN_VALUES,
    EMPRESA_STATUS_VALUES,
    EmpresaAdminCreateRequest,
    EmpresaAdminListResponse,
    EmpresaAdminSummary,
    EmpresaAdminUpdateRequest,
    EmpresaStatusUpdateRequest,
    GlobalDashboardResponse,
)
from app.modules.admin.security import (
    build_admin_context_from_user,
    create_admin_access_token,
    create_admin_refresh_token,
    hash_admin_refresh_token,
)
from app.modules.companies.models import Empresa

logger = logging.getLogger("ai_sales_agent.admin")


# ─────────────────────────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────────────────────────


class AdminAuthService:
    def __init__(
        self,
        user_repo: AdminUserRepository,
        refresh_repo: AdminRefreshTokenRepository,
        audit_repo: AdminAuditRepository,
    ) -> None:
        self._users = user_repo
        self._refresh = refresh_repo
        self._audit = audit_repo

    async def login(
        self, payload: AdminLoginRequest, *, ip_address: str | None = None
    ) -> AdminAuthSessionResponse:
        user = await self._users.get_by_email(email=payload.email)
        if user is None or not verify_password(payload.password, user.password_hash):
            logger.warning("Failed admin login attempt for email=%s", payload.email)
            raise AppError(
                code="invalid_credentials",
                message="Invalid email or password",
                status_code=401,
            )
        if not user.is_active:
            raise AppError(
                code="account_disabled", message="Admin account is not active", status_code=403
            )

        await self._users.update_last_login(user=user)

        # Generar access + refresh token
        access_token = create_admin_access_token(
            user_id=user.id, email=user.email, roles=[user.rol]
        )
        refresh_token, refresh_hash, family_id, expires_at = create_admin_refresh_token()
        await self._refresh.create(
            admin_user_id=user.id,
            token_hash=refresh_hash,
            family_id=family_id,
            expires_at=expires_at,
        )

        ctx = build_admin_context_from_user(user=user)
        await self._audit.record(
            admin_user_id=user.id,
            action="admin_login",
            target_empresa_id=None,
            details={"event": "admin_login"},
            ip_address=ip_address,
        )
        await self._refresh.commit()

        return AdminAuthSessionResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=get_settings().access_token_expire_minutes * 60,
            user=AdminCurrentUserResponse(
                user_id=user.id,
                email=user.email,
                roles=ctx.roles,
                permissions=sorted(ctx.permissions),
                is_super_admin=ctx.is_super_admin,
            ),
        )

    async def refresh(self, payload: AdminRefreshRequest) -> AdminTokenResponse:
        token_hash = hash_admin_refresh_token(payload.refresh_token)
        record = await self._refresh.get_active(token_hash=token_hash)
        if record is None:
            stale = await self._refresh.get_by_hash(token_hash=token_hash)
            if stale is not None:
                await self._refresh.revoke_family(family_id=stale.family_id)
                await self._refresh.commit()
            raise AppError(
                code="invalid_refresh_token", message="Invalid refresh token", status_code=401
            )

        user = await self._users.get_by_id(user_id=record.admin_user_id)
        if user is None or not user.is_active:
            await self._refresh.revoke_family(family_id=record.family_id)
            await self._refresh.commit()
            raise AppError(
                code="invalid_session", message="Session is no longer valid", status_code=401
            )

        new_token, new_hash, _, new_exp = create_admin_refresh_token()
        new_record = await self._refresh.create(
            admin_user_id=user.id,
            token_hash=new_hash,
            family_id=record.family_id,
            expires_at=new_exp,
        )
        await self._refresh.revoke(token=record, replaced_by=new_record.id)

        access_token = create_admin_access_token(
            user_id=user.id, email=user.email, roles=[user.rol]
        )
        await self._refresh.commit()

        return AdminTokenResponse(
            access_token=access_token,
            refresh_token=new_token,
            expires_in=get_settings().access_token_expire_minutes * 60,
        )

    async def logout(self, payload: AdminLogoutRequest) -> None:
        record = await self._refresh.get_by_hash(
            token_hash=hash_admin_refresh_token(payload.refresh_token)
        )
        if record is not None and record.revoked_at is None:
            await self._refresh.revoke(token=record)
            await self._refresh.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Tenant management
# ─────────────────────────────────────────────────────────────────────────────


class AdminService:
    def __init__(
        self,
        empresas_repo: EmpresaAdminRepository,
        audit_repo: AdminAuditRepository,
        user_repo: AdminUserRepository,
    ) -> None:
        self._empresas = empresas_repo
        self._audit = audit_repo
        self._users = user_repo

    async def list_empresas(
        self,
        *,
        limit: int,
        offset: int,
        search: str | None,
        status: str | None,
        plan: str | None,
    ) -> EmpresaAdminListResponse:
        items, total = await self._empresas.list_all(
            limit=limit, offset=offset, search=search, status=status, plan=plan
        )
        return EmpresaAdminListResponse(
            items=[_empresa_to_summary(e) for e in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def create_empresa(
        self,
        *,
        admin_user_id: UUID,
        payload: EmpresaAdminCreateRequest,
        ip_address: str | None = None,
    ) -> EmpresaAdminSummary:
        if payload.plan not in EMPRESA_PLAN_VALUES:
            raise AppError(
                code="invalid_plan",
                message=f"Plan must be one of {EMPRESA_PLAN_VALUES}",
                status_code=400,
            )
        if payload.status not in EMPRESA_STATUS_VALUES:
            raise AppError(
                code="invalid_status",
                message=f"Status must be one of {EMPRESA_STATUS_VALUES}",
                status_code=400,
            )

        empresa = Empresa(
            id=uuid4(),
            nombre=payload.nombre,
            slug=payload.slug,
            plan=payload.plan,
            logo_url=payload.logo_url,
            estado=payload.status,
        )
        try:
            self._empresas._session.add(empresa)
            await self._empresas._session.flush()
            await self._empresas._session.refresh(empresa)
        except IntegrityError as exc:
            await self._empresas.rollback()
            raise AppError(
                code="empresa_conflict",
                message="A company with that slug already exists",
                status_code=409,
            ) from exc

        await self._audit.record(
            admin_user_id=admin_user_id,
            action="company_created",
            target_empresa_id=empresa.id,
            details={
                "nombre": empresa.nombre,
                "slug": empresa.slug,
                "plan": empresa.plan,
                "status": empresa.estado,
            },
            ip_address=ip_address,
        )
        await self._empresas.commit()
        return _empresa_to_summary(empresa)

    async def update_empresa(
        self,
        *,
        admin_user_id: UUID,
        empresa_id: UUID,
        payload: EmpresaAdminUpdateRequest,
        ip_address: str | None = None,
    ) -> EmpresaAdminSummary:
        empresa = await self._get_empresa_or_404(empresa_id=empresa_id)
        previous = {
            "nombre": empresa.nombre,
            "plan": empresa.plan,
            "logo_url": empresa.logo_url,
            "status": empresa.estado,
        }

        if payload.plan is not None and payload.plan not in EMPRESA_PLAN_VALUES:
            raise AppError(
                code="invalid_plan",
                message=f"Plan must be one of {EMPRESA_PLAN_VALUES}",
                status_code=400,
            )
        if payload.status is not None and payload.status not in EMPRESA_STATUS_VALUES:
            raise AppError(
                code="invalid_status",
                message=f"Status must be one of {EMPRESA_STATUS_VALUES}",
                status_code=400,
            )

        await self._empresas.update_fields(
            empresa=empresa,
            nombre=payload.nombre,
            plan=payload.plan,
            logo_url=payload.logo_url,
            status=payload.status,
        )
        await self._empresas._session.refresh(empresa)

        await self._audit.record(
            admin_user_id=admin_user_id,
            action="company_updated",
            target_empresa_id=empresa.id,
            details={"before": previous, "after": payload.model_dump(exclude_unset=True)},
            ip_address=ip_address,
        )
        await self._empresas.commit()
        return _empresa_to_summary(empresa)

    async def update_status(
        self,
        *,
        admin_user_id: UUID,
        empresa_id: UUID,
        payload: EmpresaStatusUpdateRequest,
        ip_address: str | None = None,
    ) -> EmpresaAdminSummary:
        if payload.status not in EMPRESA_STATUS_VALUES:
            raise AppError(
                code="invalid_status",
                message=f"Status must be one of {EMPRESA_STATUS_VALUES}",
                status_code=400,
            )
        empresa = await self._get_empresa_or_404(empresa_id=empresa_id)
        previous = empresa.estado
        await self._empresas.update_status(empresa=empresa, status=payload.status)
        await self._empresas._session.refresh(empresa)

        action_map = {
            "active": "company_activated",
            "suspended": "company_suspended",
            "expired": "company_expired",
        }
        await self._audit.record(
            admin_user_id=admin_user_id,
            action=action_map[payload.status],
            target_empresa_id=empresa.id,
            details={"from": previous, "to": payload.status},
            ip_address=ip_address,
        )
        await self._empresas.commit()
        return _empresa_to_summary(empresa)

    async def get_empresa(self, *, empresa_id: UUID) -> EmpresaAdminSummary:
        empresa = await self._get_empresa_or_404(empresa_id=empresa_id)
        return _empresa_to_summary(empresa)

    async def _get_empresa_or_404(self, *, empresa_id: UUID) -> Empresa:
        empresa = await self._empresas.get_by_id(empresa_id=empresa_id)
        if empresa is None:
            raise AppError(
                code="empresa_not_found", message="Company not found", status_code=404
            )
        return empresa


# ─────────────────────────────────────────────────────────────────────────────
# Audit
# ─────────────────────────────────────────────────────────────────────────────


class AdminAuditService:
    def __init__(self, repo: AdminAuditRepository) -> None:
        self._repo = repo

    async def list_entries(
        self,
        *,
        limit: int,
        offset: int,
        action: str | None,
        admin_user_id: UUID | None,
        target_empresa_id: UUID | None,
    ) -> AdminAuditListResponse:
        items, total = await self._repo.list(
            limit=limit,
            offset=offset,
            action=action,
            admin_user_id=admin_user_id,
            target_empresa_id=target_empresa_id,
        )
        return AdminAuditListResponse(
            items=[AdminAuditEntryResponse.model_validate(e) for e in items],
            total=total,
            limit=limit,
            offset=offset,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Global dashboard
# ─────────────────────────────────────────────────────────────────────────────


class GlobalMetricsService:
    def __init__(
        self,
        empresas_repo: EmpresaAdminRepository,
        metrics_repo: GlobalMetricsRepository,
    ) -> None:
        self._empresas = empresas_repo
        self._metrics = metrics_repo

    async def dashboard(self) -> GlobalDashboardResponse:
        by_status = await self._empresas.count_by_status()
        by_plan = await self._empresas.count_by_plan()
        total = sum(by_status.values())
        return GlobalDashboardResponse(
            total_empresas=total,
            empresas_activas=by_status.get("active", 0),
            empresas_suspendidas=by_status.get("suspended", 0),
            empresas_expiradas=by_status.get("expired", 0),
            total_clientes=await self._metrics.total_clientes(),
            total_pedidos=await self._metrics.total_pedidos(),
            total_conversaciones=await self._metrics.total_conversaciones(),
            total_ventas=await self._metrics.total_ventas(),
            planes_breakdown=by_plan,
            status_breakdown=by_status,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _empresa_to_summary(empresa: Empresa) -> EmpresaAdminSummary:
    return EmpresaAdminSummary(
        id=empresa.id,
        nombre=empresa.nombre,
        slug=empresa.slug,
        plan=getattr(empresa, "plan", DEFAULT_EMPRESA_PLAN) or DEFAULT_EMPRESA_PLAN,
        status=getattr(empresa, "estado", DEFAULT_EMPRESA_STATUS) or DEFAULT_EMPRESA_STATUS,
        logo_url=getattr(empresa, "logo_url", None),
        created_at=empresa.created_at,
        updated_at=empresa.updated_at,
    )


__all__ = [
    "AdminAuditService",
    "AdminAuthService",
    "AdminService",
    "GlobalMetricsService",
    "EMPRESA_PLANS",
    "EMPRESA_STATUS",
    "SUPER_ADMIN_ROLE",
]
