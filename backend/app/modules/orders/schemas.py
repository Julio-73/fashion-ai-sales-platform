from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

OrderStatus = Literal["pending", "confirmed", "preparing", "shipped", "delivered", "cancelled"]
DeliveryType = Literal["delivery", "store_pickup"]


class OrderItemCreateRequest(BaseModel):
    product_id: UUID | None = None
    product_name: str = Field(min_length=1, max_length=180)
    size: str | None = Field(default=None, max_length=32)
    color: str | None = Field(default=None, max_length=48)
    quantity: int = Field(default=1, ge=1)
    price: Decimal = Field(default=Decimal("0"), ge=0)


class OrderCreateRequest(BaseModel):
    customer_name: str = Field(min_length=1, max_length=180)
    customer_phone: str | None = Field(default=None, max_length=40)
    delivery_type: DeliveryType
    delivery_address: str | None = Field(default=None, max_length=1000)
    status: OrderStatus = "confirmed"
    items: list[OrderItemCreateRequest] = Field(min_length=1)


class OrderStatusUpdateRequest(BaseModel):
    status: OrderStatus


class OrderItemResponse(BaseModel):
    id: UUID
    order_id: UUID
    empresa_id: UUID
    product_id: UUID | None
    product_name: str
    size: str | None
    color: str | None
    quantity: int
    price: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    order_number: str
    customer_name: str
    customer_phone: str | None
    delivery_type: str
    delivery_address: str | None
    status: OrderStatus
    total: Decimal
    items: list[OrderItemResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    total: int
    limit: int
    offset: int


class OrderMetricsResponse(BaseModel):
    orders_today: int
    orders_week: int
    orders_month: int
    total_sales: Decimal


class OrderFilters(BaseModel):
    status: OrderStatus | None = None
    customer: str | None = None
    date_from: date | None = None
    date_to: date | None = None
