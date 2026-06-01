from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TenantMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Order(UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("empresa_id", "order_number", name="uq_orders__empresa_id_order_number"),
        Index("idx_orders__empresa_id_created_at", "empresa_id", "created_at"),
        Index("idx_orders__empresa_id_status", "empresa_id", "status"),
        Index("idx_orders__empresa_id_customer_name", "empresa_id", "customer_name"),
    )

    order_number: Mapped[str] = mapped_column(String(40), nullable=False)
    customer_name: Mapped[str] = mapped_column(String(180), nullable=False)
    customer_phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    delivery_type: Mapped[str] = mapped_column(String(40), nullable=False)
    delivery_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderItem.created_at",
    )


class OrderItem(UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "order_items"
    __table_args__ = (
        Index("idx_order_items__order_id", "order_id"),
        Index("idx_order_items__empresa_id_order_id", "empresa_id", "order_id"),
        Index("idx_order_items__empresa_id_product_id", "empresa_id", "product_id"),
    )

    order_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("productos.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    product_name: Mapped[str] = mapped_column(String(180), nullable=False)
    size: Mapped[str | None] = mapped_column(String(32), nullable=True)
    color: Mapped[str | None] = mapped_column(String(48), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    order: Mapped[Order] = relationship(back_populates="items")
