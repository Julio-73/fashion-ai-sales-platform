"""add sales pipeline items table

Revision ID: 0015_sales_pipeline
Revises: 0014_ai_live_fk_core
Create Date: 2026-06-04

SALES PIPELINE ENTERPRISE V1 - new ``sales_pipeline_items`` table.

Additive migration. Does not modify or drop any existing table.

The table is the materialised view of a sales "deal" going through a
funnel of stages. It denormalises the bare minimum from ``clientes``,
``conversations_core`` and ``orders`` to power a kanban-style pipeline
without requiring complex joins at the UI layer.

Stages (CHECK constraint, see ``app/modules/pipeline/models.py``):
    new_lead, contacted, qualified, proposal, negotiation, won, lost.
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "0015_sales_pipeline"
down_revision: str | None = "0014_ai_live_fk_core"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


PIPELINE_STAGE_VALUES = (
    "new_lead",
    "contacted",
    "qualified",
    "proposal",
    "negotiation",
    "won",
    "lost",
)


def upgrade() -> None:
    op.create_table(
        "sales_pipeline_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clientes.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("conversations_core.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("estimated_value", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("probability", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("stage", sa.String(length=32), nullable=False, server_default=sa.text("'new_lead'")),
        sa.Column("stage_entered_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("won_reason", sa.String(length=120), nullable=True),
        sa.Column("lost_reason", sa.String(length=120), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("channel", sa.String(length=32), nullable=True),
        sa.Column("is_vip", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "stage in ('new_lead', 'contacted', 'qualified', 'proposal', 'negotiation', 'won', 'lost')",
            name="ck_sales_pipeline_items__stage",
        ),
        sa.CheckConstraint(
            "probability between 0 and 100",
            name="ck_sales_pipeline_items__probability",
        ),
        sa.CheckConstraint(
            "estimated_value >= 0",
            name="ck_sales_pipeline_items__estimated_value",
        ),
    )
    op.create_index(
        "idx_sales_pipeline_items__empresa_stage_last",
        "sales_pipeline_items",
        ["empresa_id", "stage", "last_activity_at"],
    )
    op.create_index(
        "idx_sales_pipeline_items__empresa_stage_entered",
        "sales_pipeline_items",
        ["empresa_id", "stage_entered_at"],
    )
    op.create_index(
        "idx_sales_pipeline_items__empresa_customer",
        "sales_pipeline_items",
        ["empresa_id", "customer_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_sales_pipeline_items__empresa_customer", table_name="sales_pipeline_items")
    op.drop_index("idx_sales_pipeline_items__empresa_stage_entered", table_name="sales_pipeline_items")
    op.drop_index("idx_sales_pipeline_items__empresa_stage_last", table_name="sales_pipeline_items")
    op.drop_table("sales_pipeline_items")


__all__ = ["upgrade", "downgrade"]
