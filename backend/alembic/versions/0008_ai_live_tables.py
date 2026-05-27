"""add ai_live tables for conversation AI states and events

Revision ID: 0008_ai_live_tables
Revises: 0007_sales_intelligence_fields
Create Date: 2026-05-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008_ai_live_tables"
down_revision: str | None = "0007_sales_intelligence_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "conversation_ai_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("ai_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("auto_reply_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("escalation_required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("last_detected_intent", sa.String(64), nullable=True),
        sa.Column("sentiment", sa.String(32), nullable=True),
        sa.Column("urgency_score", sa.Float(), nullable=True),
        sa.Column("lead_temperature", sa.String(16), nullable=True),
        sa.Column("ai_last_response", sa.Text(), nullable=True),
        sa.Column("ai_confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("empresa_id", "conversation_id", name="uq_ai_state_tenant_conversation"),
    )
    op.create_index(
        "idx_ai_state__empresa_conversation",
        "conversation_ai_states",
        ["empresa_id", "conversation_id"],
    )

    op.create_table(
        "conversation_ai_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("event_type", sa.String(48), nullable=False),
        sa.Column("payload", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "idx_ai_event__empresa_conversation",
        "conversation_ai_events",
        ["empresa_id", "conversation_id"],
    )
    op.create_index(
        "idx_ai_event__created_at",
        "conversation_ai_events",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_table("conversation_ai_events")
    op.drop_table("conversation_ai_states")
