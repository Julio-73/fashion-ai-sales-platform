"""add admin enterprise module

Revision ID: 0013_admin_enterprise
Revises: 0012_whatsapp_business
Create Date: 2026-06-04

Additive: añade ``plan`` y ``logo_url`` a ``empresas`` y crea las tablas
del módulo Admin Enterprise (``admin_users``, ``admin_refresh_tokens``,
``admin_audit_log``). No modifica ninguna tabla congelada.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "0013_admin_enterprise"
down_revision: str | None = "0012_whatsapp_business"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # empresas: añadir columnas plan y logo_url (aditivo)
    # ------------------------------------------------------------------
    op.add_column(
        "empresas",
        sa.Column(
            "plan",
            sa.String(length=32),
            nullable=False,
            server_default="basic",
        ),
    )
    op.add_column(
        "empresas",
        sa.Column("logo_url", sa.String(length=512), nullable=True),
    )
    op.create_check_constraint(
        "ck_empresas__plan",
        "empresas",
        "plan in ('basic', 'pro', 'enterprise')",
    )
    op.create_check_constraint(
        "ck_empresas__estado",
        "empresas",
        "estado in ('active', 'suspended', 'expired')",
    )

    # ------------------------------------------------------------------
    # admin_users — cuentas de Super Admin / Company Admin
    # ------------------------------------------------------------------
    op.create_table(
        "admin_users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=160), nullable=True),
        sa.Column(
            "rol",
            sa.String(length=32),
            nullable=False,
            server_default="super_admin",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "rol in ('super_admin', 'company_admin', 'agent')",
            name="ck_admin_users__rol",
        ),
    )
    op.create_index("idx_admin_users__email", "admin_users", ["email"], unique=True)

    # ------------------------------------------------------------------
    # admin_refresh_tokens — refresh tokens opacos (aislados de los tenant)
    # ------------------------------------------------------------------
    op.create_table(
        "admin_refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "admin_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admin_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(length=255), nullable=False, unique=True),
        sa.Column("family_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "replaced_by_token_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_admin_refresh_tokens__admin_user_id",
        "admin_refresh_tokens",
        ["admin_user_id"],
    )
    op.create_index(
        "idx_admin_refresh_tokens__family_id",
        "admin_refresh_tokens",
        ["family_id"],
    )

    # ------------------------------------------------------------------
    # admin_audit_log — registro inmutable de acciones del super admin
    # ------------------------------------------------------------------
    op.create_table(
        "admin_audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "admin_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admin_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "target_empresa_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("empresas.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action", sa.String(length=48), nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_admin_audit_log__admin_user_id_created_at",
        "admin_audit_log",
        ["admin_user_id", "created_at"],
    )
    op.create_index(
        "idx_admin_audit_log__target_empresa_id_created_at",
        "admin_audit_log",
        ["target_empresa_id", "created_at"],
    )
    op.create_index(
        "idx_admin_audit_log__action_created_at",
        "admin_audit_log",
        ["action", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_admin_audit_log__action_created_at", table_name="admin_audit_log")
    op.drop_index(
        "idx_admin_audit_log__target_empresa_id_created_at", table_name="admin_audit_log"
    )
    op.drop_index(
        "idx_admin_audit_log__admin_user_id_created_at", table_name="admin_audit_log"
    )
    op.drop_table("admin_audit_log")

    op.drop_index("idx_admin_refresh_tokens__family_id", table_name="admin_refresh_tokens")
    op.drop_index("idx_admin_refresh_tokens__admin_user_id", table_name="admin_refresh_tokens")
    op.drop_table("admin_refresh_tokens")

    op.drop_index("idx_admin_users__email", table_name="admin_users")
    op.drop_table("admin_users")

    op.drop_constraint("ck_empresas__estado", "empresas", type_="check")
    op.drop_constraint("ck_empresas__plan", "empresas", type_="check")
    op.drop_column("empresas", "logo_url")
    op.drop_column("empresas", "plan")
