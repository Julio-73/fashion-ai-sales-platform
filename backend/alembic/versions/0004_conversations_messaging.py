"""conversations and messaging

Revision ID: 0004_conversations_messaging
Revises: 0003_enterprise_products_catalog
Create Date: 2026-05-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_conversations_messaging"
down_revision: str | None = "0003_enterprise_products_catalog"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("cliente_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("asunto", sa.String(length=240), nullable=True),
        sa.Column("canal", sa.String(length=32), nullable=False),
        sa.Column("estado", sa.String(length=32), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["cliente_id"], ["clientes.id"], name="fk_conversations__cliente_id__clientes", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], name="fk_conversations__empresa_id__empresas", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_conversations"),
    )
    op.create_index("idx_conversations__empresa_id_estado_updated_at", "conversations", ["empresa_id", "estado", "updated_at"])
    op.create_index("idx_conversations__empresa_id_cliente_id", "conversations", ["empresa_id", "cliente_id"])

    op.create_table(
        "messages",
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sender_name", sa.String(length=160), nullable=True),
        sa.Column("extra_data", postgresql.JSONB, nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], name="fk_messages__empresa_id__empresas", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], name="fk_messages__conversation_id__conversations", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_messages"),
    )
    op.create_index("idx_messages__conversation_id_created_at", "messages", ["conversation_id", "created_at"])


def downgrade() -> None:
    op.drop_index("idx_messages__conversation_id_created_at", table_name="messages")
    op.drop_table("messages")

    op.drop_index("idx_conversations__empresa_id_cliente_id", table_name="conversations")
    op.drop_index("idx_conversations__empresa_id_estado_updated_at", table_name="conversations")
    op.drop_table("conversations")
