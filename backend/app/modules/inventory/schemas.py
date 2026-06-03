"""Pydantic schemas for the Inventory Management module."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

InventoryStatus = Literal["normal", "stock_bajo", "agotado"]
InventoryStatusFilter = Literal["all", "normal", "stock_bajo", "agotado"]
InventorySortBy = Literal["name", "stock_actual", "stock_disponible", "last_movement_at", "category"]
MovementTipo = Literal["entrada", "salida", "reserva", "liberacion", "ajuste"]
ReservationStatusLiteral = Literal["active", "cancelled", "released", "expired"]


class InventoryItemBase(BaseModel):
    stock_actual: int = Field(default=0, ge=0)
    stock_minimo: int = Field(default=0, ge=0)
    stock_reservado: int = Field(default=0, ge=0)


class InventoryItemResponse(BaseModel):
    product_id: UUID
    stock_actual: int
    stock_minimo: int
    stock_reservado: int
    stock_disponible: int
    status: InventoryStatus
    last_movement_at: datetime | None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InventoryItemUpdateRequest(BaseModel):
    stock_actual: int | None = Field(default=None, ge=0)
    stock_minimo: int | None = Field(default=None, ge=0)
    motivo: str | None = Field(default=None, max_length=255)


class InventoryMovementResponse(BaseModel):
    id: UUID
    product_id: UUID
    tipo: MovementTipo
    cantidad: int
    motivo: str | None
    ref_type: str | None
    ref_id: UUID | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InventoryReservationCreateRequest(BaseModel):
    product_id: UUID
    quantity: int = Field(ge=1)
    ref_type: str | None = Field(default=None, max_length=32)
    ref_id: UUID | None = None
    expires_at: datetime | None = None


class InventoryReservationResponse(BaseModel):
    id: UUID
    product_id: UUID
    quantity: int
    status: ReservationStatusLiteral
    ref_type: str | None
    ref_id: UUID | None
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InventoryProductSummary(BaseModel):
    product_id: UUID
    name: str
    category: str | None
    base_price: Decimal | None
    sku: str | None
    image_url: str | None
    stock_actual: int
    stock_minimo: int
    stock_reservado: int
    stock_disponible: int
    status: InventoryStatus
    last_movement_at: datetime | None
    updated_at: datetime


class InventoryListResponse(BaseModel):
    items: list[InventoryProductSummary]
    total: int
    limit: int
    offset: int


class InventoryProductDetailResponse(BaseModel):
    product: InventoryProductSummary
    recent_movements: list[InventoryMovementResponse]
    active_reservations: list[InventoryReservationResponse]
    metrics: InventoryAggregateMetrics


class InventoryAggregateMetrics(BaseModel):
    total_products: int
    out_of_stock: int
    low_stock: int
    normal_stock: int
    inventory_value: Decimal
    total_units: int
    total_reserved_units: int
    top_selling_products: list[InventoryTopProductMetric]
    lowest_stock_products: list[InventoryLowStockProduct]


class InventoryTopProductMetric(BaseModel):
    product_id: UUID
    name: str
    units_sold: int
    revenue: Decimal


class InventoryLowStockProduct(BaseModel):
    product_id: UUID
    name: str
    stock_actual: int
    stock_minimo: int
    status: InventoryStatus


# Re-export helpers ---------------------------------------------------------


def classify_status(*, stock_actual: int, stock_minimo: int) -> InventoryStatus:
    if stock_actual <= 0:
        return "agotado"
    if stock_actual <= stock_minimo:
        return "stock_bajo"
    return "normal"
