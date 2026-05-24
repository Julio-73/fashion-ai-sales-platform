from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TenantMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Producto(UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "productos"
    __table_args__ = (
        UniqueConstraint("empresa_id", "slug", name="uq_productos__empresa_id_slug"),
        Index("idx_productos__empresa_id_created_at", "empresa_id", "created_at"),
        Index("idx_productos__empresa_id_category", "empresa_id", "category"),
        Index("idx_productos__empresa_id_status", "empresa_id", "status"),
    )

    name: Mapped[str] = mapped_column(String(180), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    base_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    variants: Mapped[list["ProductVariant"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductVariant.created_at",
    )
    images: Mapped[list["ProductImage"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductImage.order_index",
    )


class ProductVariant(UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "product_variants"
    __table_args__ = (
        UniqueConstraint("empresa_id", "sku", name="uq_product_variants__empresa_id_sku"),
        Index("idx_product_variants__product_id", "product_id"),
        Index("idx_product_variants__empresa_id_product_id", "empresa_id", "product_id"),
    )

    product_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("productos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    talla: Mapped[str | None] = mapped_column(String(32), nullable=True)
    color: Mapped[str | None] = mapped_column(String(48), nullable=True)
    sku: Mapped[str] = mapped_column(String(80), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reserved_stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    variant_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    product: Mapped["Producto"] = relationship(back_populates="variants")

    @property
    def available_stock(self) -> int:
        return self.stock - self.reserved_stock


class ProductImage(UUIDPrimaryKeyMixin, TenantMixin, Base):
    __tablename__ = "product_images"
    __table_args__ = (
        Index("idx_product_images__product_id", "product_id"),
        Index("idx_product_images__empresa_id_product_id", "empresa_id", "product_id"),
    )

    product_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("productos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    image_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    product: Mapped["Producto"] = relationship(back_populates="images")
