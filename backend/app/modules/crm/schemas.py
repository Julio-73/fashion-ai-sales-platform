"""CRM Enterprise V1 — Customer 360 schemas.

This module is additive: it does not modify the existing customers module.
It joins the existing ``clientes`` and ``orders`` tables on a normalized
``customer_name`` match to compute Customer 360 analytics.
"""
from __future__ import annotations

from datetime import date, datetime  # noqa: F401  (date is used in router query types)
from decimal import Decimal
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CustomerLifecycleStatus(str, Enum):
    """Computed customer lifecycle status derived from order analytics."""

    NUEVO = "nuevo"
    ACTIVO = "activo"
    RECURRENTE = "recurrente"
    VIP = "vip"
    INACTIVO = "inactivo"


# Filter / sort literals exposed via query parameters.
CustomerStatusFilter = Literal["all", "nuevo", "activo", "recurrente", "vip", "inactivo"]
CustomerSortBy = Literal["created_at", "full_name", "lifetime_value", "last_purchase_at", "order_count"]


class CustomerMetrics(BaseModel):
    """Aggregated commercial metrics for a single customer."""

    order_count: int = Field(default=0, ge=0)
    lifetime_value: Decimal = Field(default=Decimal("0"), ge=0)
    average_ticket: Decimal = Field(default=Decimal("0"), ge=0)
    first_purchase_at: datetime | None = None
    last_purchase_at: datetime | None = None
    days_since_last_purchase: int | None = None
    status: CustomerLifecycleStatus


class Customer360Summary(BaseModel):
    """Customer profile enriched with computed Customer 360 metrics."""

    id: UUID
    empresa_id: UUID
    full_name: str
    email: EmailStr | None
    phone: str | None
    whatsapp: str | None
    instagram_username: str | None
    tags: list[str]
    notes: str | None
    lead_status: str
    source: str | None
    assigned_to: UUID | None
    created_at: datetime
    updated_at: datetime
    metrics: CustomerMetrics

    model_config = ConfigDict(from_attributes=True)


class Customer360ListResponse(BaseModel):
    items: list[Customer360Summary]
    total: int
    limit: int
    offset: int
    aggregate: CustomerAggregateMetrics


class CustomerAggregateMetrics(BaseModel):
    """Aggregate metrics over a filtered customer set."""

    total_customers: int = 0
    new_customers: int = 0
    active_customers: int = 0
    recurrent_customers: int = 0
    vip_customers: int = 0
    inactive_customers: int = 0
    total_lifetime_value: Decimal = Decimal("0")
    average_ticket: Decimal = Decimal("0")
    average_orders_per_customer: Decimal = Decimal("0")


class CustomerOrderHistoryItem(BaseModel):
    order_id: UUID
    order_number: str
    created_at: datetime
    status: str
    total: Decimal
    items_count: int
    primary_product_name: str


class CustomerOrderHistoryResponse(BaseModel):
    customer_id: UUID
    total: int
    limit: int
    offset: int
    items: list[CustomerOrderHistoryItem]
