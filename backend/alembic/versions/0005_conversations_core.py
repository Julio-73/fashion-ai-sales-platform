"""conversations core system

Revision ID: 0005_conversations_core
Revises: 0004_conversations_messaging
Create Date: 2026-05-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_conversations_core"
down_revision: str | None = "0004_conversations_messaging"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "conversations_core",
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("last_message", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["clientes.id"], name="fk_convcore__customer_id__clientes", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], name="fk_convcore__empresa_id__empresas", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_conversations_core"),
    )
    op.create_index("idx_convcore__empresa_id_status_updated_at", "conversations_core", ["empresa_id", "status", "updated_at"])
    op.create_index("idx_convcore__empresa_id_customer_id", "conversations_core", ["empresa_id", "customer_id"])

    op.create_table(
        "messages_core",
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sender", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], name="fk_msgcore__empresa_id__empresas", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations_core.id"], name="fk_msgcore__conversation_id__convcore", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_messages_core"),
    )
    op.create_index("idx_msgcore__conversation_id_created_at", "messages_core", ["conversation_id", "created_at"])


def downgrade() -> None:
    op.drop_index("idx_msgcore__conversation_id_created_at", table_name="messages_core")
    op.drop_table("messages_core")

    op.drop_index("idx_convcore__empresa_id_customer_id", table_name="conversations_core")
    op.drop_index("idx_convcore__empresa_id_status_updated_at", table_name="conversations_core")
    op.drop_table("conversations_core")
