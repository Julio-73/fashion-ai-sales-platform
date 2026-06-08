"""Schemas Pydantic (request/response) del módulo Admin Enterprise."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# ─────────────────────────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────────────────────────


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class AdminRefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=32)


class AdminLogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=32)


class AdminTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AdminCurrentUserResponse(BaseModel):
    user_id: UUID
    email: EmailStr
    roles: list[str]
    permissions: list[str]
    is_super_admin: bool

    model_config = ConfigDict(from_attributes=True)


class AdminAuthSessionResponse(AdminTokenResponse):
    user: AdminCurrentUserResponse


# ─────────────────────────────────────────────────────────────────────────────
# Empresa / Tenant
# ─────────────────────────────────────────────────────────────────────────────


EMPRESA_STATUS_VALUES = ("active", "suspended", "expired")
EMPRESA_PLAN_VALUES = ("basic", "pro", "enterprise")


class EmpresaAdminSummary(BaseModel):
    id: UUID
    nombre: str
    slug: str
    plan: str
    status: str
    logo_url: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmpresaAdminListResponse(BaseModel):
    items: list[EmpresaAdminSummary]
    total: int
    limit: int
    offset: int


class EmpresaAdminCreateRequest(BaseModel):
    nombre: str = Field(min_length=2, max_length=160)
    slug: str = Field(
        min_length=2,
        max_length=120,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    plan: str = Field(default="basic")
    logo_url: str | None = Field(default=None, max_length=512)
    status: str = Field(default="active")


class EmpresaAdminUpdateRequest(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=160)
    plan: str | None = Field(default=None)
    logo_url: str | None = Field(default=None, max_length=512)
    status: str | None = Field(default=None)


class EmpresaStatusUpdateRequest(BaseModel):
    status: str


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard global
# ─────────────────────────────────────────────────────────────────────────────


class GlobalDashboardResponse(BaseModel):
    total_empresas: int
    empresas_activas: int
    empresas_suspendidas: int
    empresas_expiradas: int
    total_clientes: int
    total_pedidos: int
    total_conversaciones: int
    total_ventas: float
    planes_breakdown: dict[str, int]
    status_breakdown: dict[str, int]


# ─────────────────────────────────────────────────────────────────────────────
# Audit log
# ─────────────────────────────────────────────────────────────────────────────


class AdminAuditEntryResponse(BaseModel):
    id: UUID
    admin_user_id: UUID
    admin_email: str | None = None
    target_empresa_id: UUID | None = None
    action: str
    details: dict | None = None
    ip_address: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminAuditListResponse(BaseModel):
    items: list[AdminAuditEntryResponse]
    total: int
    limit: int
    offset: int
