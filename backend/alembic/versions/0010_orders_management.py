"""add orders management tables

Revision ID: 0010_orders_management
Revises: 0009_conversation_memories
Create Date: 2026-06-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010_orders_management"
down_revision: str | None = "0009_conversation_memories"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("order_number", sa.String(40), nullable=False),
        sa.Column("customer_name", sa.String(180), nullable=False),
        sa.Column("customer_phone", sa.String(40), nullable=True),
        sa.Column("delivery_type", sa.String(40), nullable=False),
        sa.Column("delivery_address", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("total", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("empresa_id", "order_number", name="uq_orders__empresa_id_order_number"),
    )
    op.create_index("idx_orders__empresa_id_created_at", "orders", ["empresa_id", "created_at"])
    op.create_index("idx_orders__empresa_id_status", "orders", ["empresa_id", "status"])
    op.create_index("idx_orders__empresa_id_customer_name", "orders", ["empresa_id", "customer_name"])

    op.create_table(
        "order_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("productos.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("product_name", sa.String(180), nullable=False),
        sa.Column("size", sa.String(32), nullable=True),
        sa.Column("color", sa.String(48), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("price", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_order_items__order_id", "order_items", ["order_id"])
    op.create_index("idx_order_items__empresa_id_order_id", "order_items", ["empresa_id", "order_id"])
    op.create_index("idx_order_items__empresa_id_product_id", "order_items", ["empresa_id", "product_id"])


def downgrade() -> None:
    op.drop_table("order_items")
    op.drop_table("orders")
