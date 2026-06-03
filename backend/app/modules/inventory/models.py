"""SQLAlchemy models for the Inventory Management module."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TenantMixin, TimestampMixin, UUIDPrimaryKeyMixin


class MovementType(str, Enum):
    ENTRADA = "entrada"
    SALIDA = "salida"
    RESERVA = "reserva"
    LIBERACION = "liberacion"
    AJUSTE = "ajuste"


class ReservationStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    RELEASED = "released"
    EXPIRED = "expired"


class InventoryItem(UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin, Base):
    """Per-product stock snapshot (1:1 with ``productos`` per tenant)."""

    __tablename__ = "inventory_items"
    __table_args__ = (
        UniqueConstraint("empresa_id", "product_id", name="uq_inventory_items__empresa_id_product_id"),
        Index("idx_inventory_items__empresa_id_product_id", "empresa_id", "product_id"),
        CheckConstraint("stock_actual >= 0", name="ck_inventory_items__stock_actual_nonneg"),
        CheckConstraint("stock_reservado >= 0", name="ck_inventory_items__stock_reservado_nonneg"),
    )

    product_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("productos.id", ondelete="CASCADE"),
        nullable=False,
    )
    stock_actual: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stock_minimo: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stock_reservado: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_movement_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    @property
    def stock_disponible(self) -> int:
        return max(0, int(self.stock_actual) - int(self.stock_reservado))


class InventoryMovement(UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin, Base):
    """Immutable audit log of every stock change."""

    __tablename__ = "inventory_movements"
    __table_args__ = (
        CheckConstraint(
            "tipo IN ('entrada','salida','reserva','liberacion','ajuste')",
            name="ck_inventory_movements__tipo",
        ),
        Index("idx_inventory_movements__empresa_id_product_id", "empresa_id", "product_id"),
        Index("idx_inventory_movements__empresa_id_created_at", "empresa_id", "created_at"),
        Index("idx_inventory_movements__ref", "empresa_id", "ref_type", "ref_id"),
    )

    product_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("productos.id", ondelete="CASCADE"),
        nullable=False,
    )
    tipo: Mapped[str] = mapped_column(String(16), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    motivo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ref_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ref_id: Mapped[UUID | None] = mapped_column(PostgresUUID(as_uuid=True), nullable=True)


class InventoryReservation(UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin, Base):
    """Active stock holds that can be cancelled or released."""

    __tablename__ = "inventory_reservations"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active','cancelled','released','expired')",
            name="ck_inventory_reservations__status",
        ),
        CheckConstraint("quantity > 0", name="ck_inventory_reservations__quantity_pos"),
        Index("idx_inventory_reservations__empresa_id_product_id", "empresa_id", "product_id"),
        Index("idx_inventory_reservations__empresa_id_status", "empresa_id", "status"),
        Index("idx_inventory_reservations__ref", "empresa_id", "ref_type", "ref_id"),
    )

    product_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("productos.id", ondelete="CASCADE"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    ref_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ref_id: Mapped[UUID | None] = mapped_column(PostgresUUID(as_uuid=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
