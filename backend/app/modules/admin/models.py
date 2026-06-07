"""Modelos del módulo Admin Enterprise (Super Admin + Multi-empresa).

Este módulo es estrictamente aditivo. No modifica ningún modelo existente.

Las tablas nuevas NO usan ``TenantMixin`` porque un Super Admin no pertenece
a ninguna empresa concreta. La columna ``empresa_id`` se reemplaza por una
referencia opcional ``target_empresa_id`` solo en ``AdminAuditLog`` para
rastrear sobre qué tenant se realizó la acción.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, UUIDPrimaryKeyMixin


# ─────────────────────────────────────────────────────────────────────────────
# Constantes de dominio (exportadas para uso en schemas/service)
# ─────────────────────────────────────────────────────────────────────────────

ADMIN_ROLES: tuple[str, ...] = ("super_admin", "company_admin", "agent")
SUPER_ADMIN_ROLE: str = "super_admin"

EMPRESA_STATUS: tuple[str, ...] = ("active", "suspended", "expired")
EMPRESA_PLANS: tuple[str, ...] = ("basic", "pro", "enterprise")
DEFAULT_EMPRESA_PLAN: str = "basic"
DEFAULT_EMPRESA_STATUS: str = "active"

ADMIN_AUDIT_ACTIONS: tuple[str, ...] = (
    "company_created",
    "company_updated",
    "company_suspended",
    "company_activated",
    "company_expired",
    "plan_changed",
    "status_changed",
    "admin_login",
    "admin_logout",
)


# ─────────────────────────────────────────────────────────────────────────────
# Tablas
# ─────────────────────────────────────────────────────────────────────────────


class AdminUser(UUIDPrimaryKeyMixin, Base):
    """Cuenta de Super Admin / Company Admin a nivel plataforma.

    Es completamente independiente de ``usuarios`` y ``empresa_usuarios``.
    Un AdminUser NO pertenece a ninguna empresa concreta.
    """

    __tablename__ = "admin_users"
    __table_args__ = (
        Index("idx_admin_users__email", "email", unique=True),
        CheckConstraint(
            "rol in ('super_admin', 'company_admin', 'agent')",
            name="ck_admin_users__rol",
        ),
    )

    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    rol: Mapped[str] = mapped_column(String(32), nullable=False, default=SUPER_ADMIN_ROLE)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class AdminRefreshToken(UUIDPrimaryKeyMixin, Base):
    """Refresh tokens opacos (SHA-256) para sesiones de Admin.

    Aislados de ``refresh_tokens`` (tabla congelada) porque esta no permite
    un ``empresa_id`` NULL y los AdminUser no pertenecen a ninguna empresa.
    """

    __tablename__ = "admin_refresh_tokens"
    __table_args__ = (
        Index("idx_admin_refresh_tokens__admin_user_id", "admin_user_id"),
        Index("idx_admin_refresh_tokens__family_id", "family_id"),
    )

    admin_user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("admin_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    family_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), nullable=False, default=uuid.uuid4
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    replaced_by_token_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class AdminAuditLog(UUIDPrimaryKeyMixin, Base):
    """Registro inmutable de acciones del Super Admin.

    ``target_empresa_id`` es NULL cuando la acción no aplica a un tenant
    concreto (p. ej. un cambio de plan global, un login de admin, etc.).
    """

    __tablename__ = "admin_audit_log"
    __table_args__ = (
        Index("idx_admin_audit_log__admin_user_id_created_at", "admin_user_id", "created_at"),
        Index("idx_admin_audit_log__target_empresa_id_created_at", "target_empresa_id", "created_at"),
        Index("idx_admin_audit_log__action_created_at", "action", "created_at"),
    )

    admin_user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("admin_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    target_empresa_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="SET NULL"),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(String(48), nullable=False)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
