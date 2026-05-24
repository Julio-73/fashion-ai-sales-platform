"""enterprise products catalog

Revision ID: 0003_enterprise_products_catalog
Revises: 0002_enterprise_customers_crm
Create Date: 2026-05-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_enterprise_products_catalog"
down_revision: str | None = "0002_enterprise_customers_crm"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "productos",
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=80), nullable=True),
        sa.Column("base_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], name="fk_productos__empresa_id__empresas", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_productos"),
        sa.UniqueConstraint("empresa_id", "slug", name="uq_productos__empresa_id_slug"),
    )
    op.create_index("idx_productos__empresa_id", "productos", ["empresa_id"])
    op.create_index("idx_productos__empresa_id_created_at", "productos", ["empresa_id", "created_at"])
    op.create_index("idx_productos__empresa_id_category", "productos", ["empresa_id", "category"])
    op.create_index("idx_productos__empresa_id_status", "productos", ["empresa_id", "status"])

    op.create_table(
        "product_variants",
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("talla", sa.String(length=32), nullable=True),
        sa.Column("color", sa.String(length=48), nullable=True),
        sa.Column("sku", sa.String(length=80), nullable=False),
        sa.Column("stock", sa.Integer(), nullable=False),
        sa.Column("reserved_stock", sa.Integer(), nullable=False),
        sa.Column("variant_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], name="fk_product_variants__empresa_id__empresas", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_id"], ["productos.id"], name="fk_product_variants__product_id__productos", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_product_variants"),
        sa.UniqueConstraint("empresa_id", "sku", name="uq_product_variants__empresa_id_sku"),
    )
    op.create_index("idx_product_variants__empresa_id", "product_variants", ["empresa_id"])
    op.create_index("idx_product_variants__product_id", "product_variants", ["product_id"])
    op.create_index("idx_product_variants__empresa_id_product_id", "product_variants", ["empresa_id", "product_id"])

    op.create_table(
        "product_images",
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("image_url", sa.String(length=1024), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], name="fk_product_images__empresa_id__empresas", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_id"], ["productos.id"], name="fk_product_images__product_id__productos", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_product_images"),
    )
    op.create_index("idx_product_images__empresa_id", "product_images", ["empresa_id"])
    op.create_index("idx_product_images__product_id", "product_images", ["product_id"])
    op.create_index("idx_product_images__empresa_id_product_id", "product_images", ["empresa_id", "product_id"])


def downgrade() -> None:
    op.drop_index("idx_product_images__empresa_id_product_id", table_name="product_images")
    op.drop_index("idx_product_images__product_id", table_name="product_images")
    op.drop_index("idx_product_images__empresa_id", table_name="product_images")
    op.drop_table("product_images")

    op.drop_index("idx_product_variants__empresa_id_product_id", table_name="product_variants")
    op.drop_index("idx_product_variants__product_id", table_name="product_variants")
    op.drop_index("idx_product_variants__empresa_id", table_name="product_variants")
    op.drop_table("product_variants")

    op.drop_index("idx_productos__empresa_id_status", table_name="productos")
    op.drop_index("idx_productos__empresa_id_category", table_name="productos")
    op.drop_index("idx_productos__empresa_id_created_at", table_name="productos")
    op.drop_index("idx_productos__empresa_id", table_name="productos")
    op.drop_table("productos")
