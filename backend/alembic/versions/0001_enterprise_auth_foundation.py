"""enterprise auth foundation

Revision ID: 0001_enterprise_auth_foundation
Revises:
Create Date: 2026-05-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_enterprise_auth_foundation"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "empresas",
        sa.Column("nombre", sa.String(length=160), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("estado", sa.String(length=32), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_empresas"),
        sa.UniqueConstraint("slug", name="uq_empresas__slug"),
    )
    op.create_index("idx_empresas__slug", "empresas", ["slug"])

    op.create_table(
        "usuarios",
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("estado", sa.String(length=32), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_usuarios"),
        sa.UniqueConstraint("email", name="uq_usuarios__email"),
    )
    op.create_index("idx_usuarios__email", "usuarios", ["email"])

    op.create_table(
        "empresa_usuarios",
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rol", sa.String(length=64), nullable=False),
        sa.Column("estado", sa.String(length=32), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], name="fk_empresa_usuarios__empresa_id__empresas", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], name="fk_empresa_usuarios__usuario_id__usuarios", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_empresa_usuarios"),
        sa.UniqueConstraint("empresa_id", "usuario_id", name="uq_empresa_usuarios__empresa_id_usuario_id"),
    )
    op.create_index("idx_empresa_usuarios__empresa_id", "empresa_usuarios", ["empresa_id"])
    op.create_index("idx_empresa_usuarios__usuario_id", "empresa_usuarios", ["usuario_id"])
    op.create_index("idx_empresa_usuarios__usuario_id_estado", "empresa_usuarios", ["usuario_id", "estado"])

    op.create_table(
        "refresh_tokens",
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("family_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replaced_by_token_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], name="fk_refresh_tokens__empresa_id__empresas", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], name="fk_refresh_tokens__usuario_id__usuarios", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_refresh_tokens"),
        sa.UniqueConstraint("token_hash", name="uq_refresh_tokens__token_hash"),
    )
    op.create_index("idx_refresh_tokens__empresa_id", "refresh_tokens", ["empresa_id"])
    op.create_index("idx_refresh_tokens__empresa_id_usuario_id", "refresh_tokens", ["empresa_id", "usuario_id"])
    op.create_index("idx_refresh_tokens__family_id", "refresh_tokens", ["family_id"])
    op.create_index("idx_refresh_tokens__usuario_id", "refresh_tokens", ["usuario_id"])


def downgrade() -> None:
    op.drop_index("idx_refresh_tokens__usuario_id", table_name="refresh_tokens")
    op.drop_index("idx_refresh_tokens__family_id", table_name="refresh_tokens")
    op.drop_index("idx_refresh_tokens__empresa_id_usuario_id", table_name="refresh_tokens")
    op.drop_index("idx_refresh_tokens__empresa_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

    op.drop_index("idx_empresa_usuarios__usuario_id_estado", table_name="empresa_usuarios")
    op.drop_index("idx_empresa_usuarios__usuario_id", table_name="empresa_usuarios")
    op.drop_index("idx_empresa_usuarios__empresa_id", table_name="empresa_usuarios")
    op.drop_table("empresa_usuarios")

    op.drop_index("idx_usuarios__email", table_name="usuarios")
    op.drop_table("usuarios")

    op.drop_index("idx_empresas__slug", table_name="empresas")
    op.drop_table("empresas")

