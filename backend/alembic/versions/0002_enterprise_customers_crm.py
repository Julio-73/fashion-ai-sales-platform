"""enterprise customers crm

Revision ID: 0002_enterprise_customers_crm
Revises: 0001_enterprise_auth_foundation
Create Date: 2026-05-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_enterprise_customers_crm"
down_revision: str | None = "0001_enterprise_auth_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "clientes",
        sa.Column("full_name", sa.String(length=160), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("whatsapp", sa.String(length=32), nullable=True),
        sa.Column("instagram_username", sa.String(length=80), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String(length=48)), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("lead_status", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=True),
        sa.Column("assigned_to", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "lead_status in ('new', 'interested', 'negotiating', 'won', 'lost')",
            name="ck_clientes__lead_status",
        ),
        sa.ForeignKeyConstraint(["assigned_to"], ["usuarios.id"], name="fk_clientes__assigned_to__usuarios", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], name="fk_clientes__empresa_id__empresas", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_clientes"),
        sa.UniqueConstraint("empresa_id", "email", name="uq_clientes__empresa_id_email"),
    )
    op.create_index("idx_clientes__assigned_to", "clientes", ["assigned_to"])
    op.create_index("idx_clientes__empresa_id", "clientes", ["empresa_id"])
    op.create_index("idx_clientes__empresa_id_created_at", "clientes", ["empresa_id", "created_at"])
    op.create_index("idx_clientes__empresa_id_full_name", "clientes", ["empresa_id", "full_name"])
    op.create_index(
        "idx_clientes__empresa_id_lead_status_created_at",
        "clientes",
        ["empresa_id", "lead_status", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_clientes__empresa_id_lead_status_created_at", table_name="clientes")
    op.drop_index("idx_clientes__empresa_id_full_name", table_name="clientes")
    op.drop_index("idx_clientes__empresa_id_created_at", table_name="clientes")
    op.drop_index("idx_clientes__empresa_id", table_name="clientes")
    op.drop_index("idx_clientes__assigned_to", table_name="clientes")
    op.drop_table("clientes")

