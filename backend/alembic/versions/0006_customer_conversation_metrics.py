"""add customer conversation metrics

Revision ID: 0006_cust_conv_metrics
Revises: 0005_conversations_core
Create Date: 2026-05-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_cust_conv_metrics"
down_revision: str | None = "0005_conversations_core"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "clientes",
        sa.Column("last_interaction_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "clientes",
        sa.Column("conversation_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "clientes",
        sa.Column(
            "last_conversation_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_index(
        "idx_clientes__empresa_id_last_interaction_at",
        "clientes",
        ["empresa_id", "last_interaction_at"],
    )
    op.create_foreign_key(
        "fk_clientes__last_conversation_id__convcore",
        "clientes",
        "conversations_core",
        ["last_conversation_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_clientes__last_conversation_id__convcore", "clientes", type_="foreignkey")
    op.drop_index("idx_clientes__empresa_id_last_interaction_at", table_name="clientes")
    op.drop_column("clientes", "last_conversation_id")
    op.drop_column("clientes", "conversation_count")
    op.drop_column("clientes", "last_interaction_at")
