"""add inventory management tables

Revision ID: 0011_inventory_management
Revises: 0010_orders_management
Create Date: 2026-06-02
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011_inventory_management"
down_revision: str | None = "0010_orders_management"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # inventory_items — per-product stock snapshot
    # ------------------------------------------------------------------
    op.create_table(
        "inventory_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "empresa_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("empresas.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("productos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("stock_actual", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("stock_minimo", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("stock_reservado", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_movement_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("empresa_id", "product_id", name="uq_inventory_items__empresa_id_product_id"),
    )
    op.create_index("idx_inventory_items__empresa_id_product_id", "inventory_items", ["empresa_id", "product_id"])

    # ------------------------------------------------------------------
    # inventory_movements — immutable audit log
    # ------------------------------------------------------------------
    op.create_table(
        "inventory_movements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "empresa_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("empresas.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("productos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tipo",
            sa.String(16),
            nullable=False,
        ),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("motivo", sa.String(255), nullable=True),
        sa.Column("ref_type", sa.String(32), nullable=True),
        sa.Column("ref_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "tipo IN ('entrada','salida','reserva','liberacion','ajuste')",
            name="ck_inventory_movements__tipo",
        ),
    )
    op.create_index("idx_inventory_movements__empresa_id_product_id", "inventory_movements", ["empresa_id", "product_id"])
    op.create_index("idx_inventory_movements__empresa_id_created_at", "inventory_movements", ["empresa_id", "created_at"])
    op.create_index("idx_inventory_movements__ref", "inventory_movements", ["empresa_id", "ref_type", "ref_id"])

    # ------------------------------------------------------------------
    # inventory_reservations — track active holds against stock
    # ------------------------------------------------------------------
    op.create_table(
        "inventory_reservations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "empresa_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("empresas.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("productos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("ref_type", sa.String(32), nullable=True),
        sa.Column("ref_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('active','cancelled','released','expired')",
            name="ck_inventory_reservations__status",
        ),
    )
    op.create_index("idx_inventory_reservations__empresa_id_product_id", "inventory_reservations", ["empresa_id", "product_id"])
    op.create_index("idx_inventory_reservations__empresa_id_status", "inventory_reservations", ["empresa_id", "status"])
    op.create_index("idx_inventory_reservations__ref", "inventory_reservations", ["empresa_id", "ref_type", "ref_id"])


def downgrade() -> None:
    op.drop_table("inventory_reservations")
    op.drop_table("inventory_movements")
    op.drop_table("inventory_items")
