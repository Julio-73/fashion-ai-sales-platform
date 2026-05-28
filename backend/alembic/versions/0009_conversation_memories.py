"""add conversation_memories table for persistent AI memory

Revision ID: 0009_conversation_memories
Revises: 0008_ai_live_tables
Create Date: 2026-05-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009_conversation_memories"
down_revision: str | None = "0008_ai_live_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "conversation_memories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("conversations_core.id", ondelete="SET NULL"), nullable=True),
        sa.Column("memory_type", sa.String(48), nullable=False, server_default="general"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("extracted_preferences", postgresql.ARRAY(sa.String(80)), nullable=True),
        sa.Column("extracted_sizes", postgresql.ARRAY(sa.String(16)), nullable=True),
        sa.Column("extracted_colors", postgresql.ARRAY(sa.String(32)), nullable=True),
        sa.Column("extracted_styles", postgresql.ARRAY(sa.String(48)), nullable=True),
        sa.Column("extracted_occasions", postgresql.ARRAY(sa.String(48)), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("empresa_id", "customer_id", "memory_type", name="uq_memory_tenant_customer_type"),
    )
    op.create_index(
        "idx_memories__empresa_customer",
        "conversation_memories",
        ["empresa_id", "customer_id"],
    )
    op.create_index(
        "idx_memories__memory_type",
        "conversation_memories",
        ["memory_type"],
    )


def downgrade() -> None:
    op.drop_table("conversation_memories")
