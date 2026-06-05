"""Pydantic IO contracts for the Executive Dashboard module.

The schemas are intentionally flat-friendly with deeply-nested sub-objects
so the frontend can consume one round-trip payload.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Period & metadata
# ---------------------------------------------------------------------------
class ExecutivePeriod(BaseModel):
    today: datetime
    week_start: datetime
    month_start: datetime
    year_start: datetime


class ExecutiveMetadata(BaseModel):
    tenant_id: UUID
    computed_in_ms: int


# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------
class ExecutiveKPIStrip(BaseModel):
    sales_today: Decimal
    sales_week: Decimal
    sales_month: Decimal
    sales_year: Decimal
    average_ticket: Decimal
    average_ticket_month: Decimal
    active_customers: int
    vip_customers: int
    active_conversations: int
    leads_open: int
    leads_won: int
    leads_lost: int
    conversion_rate_pct: float
    total_orders: int


# ---------------------------------------------------------------------------
# Sales trend
# ---------------------------------------------------------------------------
class SalesTrendPoint(BaseModel):
    date: str
    revenue: Decimal
    orders: int


class SalesTrendMonthlyPoint(BaseModel):
    month: str
    revenue: Decimal
    orders: int


class SalesTrend(BaseModel):
    daily: list[SalesTrendPoint]
    monthly: list[SalesTrendMonthlyPoint]


# ---------------------------------------------------------------------------
# Pipeline executive view
# ---------------------------------------------------------------------------
class PipelineFunnelStage(BaseModel):
    stage: str
    label: str
    count: int
    value: Decimal
    order: int
    color: str


class ExecutivePipelineSummary(BaseModel):
    total_value: Decimal
    weighted_value: Decimal
    won_value: Decimal
    lost_value: Decimal
    conversion_pct: float
    average_time_to_close_days: float
    open_deals: int
    won_deals: int
    lost_deals: int
    funnel: list[PipelineFunnelStage]


# ---------------------------------------------------------------------------
# AI recommendations
# ---------------------------------------------------------------------------
class AIRecommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    description: str
    score: int = Field(ge=0, le=100)
    priority: Literal["high", "medium", "low"]
    category: str
    cta_label: str
    cta_href: str | None = None


# ---------------------------------------------------------------------------
# Forecast
# ---------------------------------------------------------------------------
ConfidenceLevel = Literal["low", "medium", "high"]


class ForecastBucket(BaseModel):
    projected_revenue: Decimal
    confidence: ConfidenceLevel
    basis: str
    sample_size: int


class ExecutiveForecast(BaseModel):
    monthly: ForecastBucket
    quarterly: ForecastBucket


# ---------------------------------------------------------------------------
# Top customers
# ---------------------------------------------------------------------------
class TopCustomer(BaseModel):
    id: UUID
    full_name: str
    email: str | None = None
    phone: str | None = None
    is_vip: bool = False
    order_count: int
    lifetime_value: Decimal
    average_ticket: Decimal
    days_since_last_purchase: int | None = None


# ---------------------------------------------------------------------------
# Top products
# ---------------------------------------------------------------------------
class MostSoldProduct(BaseModel):
    product_id: UUID
    name: str
    units_sold: int
    revenue: Decimal


class MostProfitableProduct(BaseModel):
    product_id: UUID
    name: str
    revenue: Decimal
    units_sold: int


class MostConsultedProduct(BaseModel):
    product_id: UUID
    name: str
    mentions: int


class TopProducts(BaseModel):
    most_sold: list[MostSoldProduct]
    most_profitable: list[MostProfitableProduct]
    most_consulted: list[MostConsultedProduct]


# ---------------------------------------------------------------------------
# Executive alerts
# ---------------------------------------------------------------------------
class InventoryCriticalAlert(BaseModel):
    product_id: UUID
    name: str
    stock: int
    min_stock: int
    status: str  # "low" | "out"


class LeadAbandonedAlert(BaseModel):
    deal_id: UUID
    title: str
    stage: str
    days_inactive: int
    value: Decimal


class ConversationUnansweredAlert(BaseModel):
    conversation_id: UUID
    customer_name: str | None
    channel: str
    last_message_at: datetime | None
    hours_silent: int


class InactiveCustomerAlert(BaseModel):
    customer_id: UUID
    full_name: str
    days_inactive: int
    last_purchase_at: datetime | None


class DelayedOrderAlert(BaseModel):
    order_id: UUID
    order_number: str
    customer_name: str
    status: str
    days_since_created: int
    total: Decimal


class ExecutiveAlerts(BaseModel):
    inventory_critical: list[InventoryCriticalAlert]
    leads_abandoned: list[LeadAbandonedAlert]
    conversations_unanswered: list[ConversationUnansweredAlert]
    inactive_customers: list[InactiveCustomerAlert]
    delayed_orders: list[DelayedOrderAlert]


# ---------------------------------------------------------------------------
# Top-level response
# ---------------------------------------------------------------------------
class ExecutiveDashboardResponse(BaseModel):
    generated_at: datetime
    period: ExecutivePeriod
    currency: str
    kpis: ExecutiveKPIStrip
    sales_trend: SalesTrend
    pipeline: ExecutivePipelineSummary
    ai_recommendations: list[AIRecommendation]
    forecast: ExecutiveForecast
    top_customers: list[TopCustomer]
    top_products: TopProducts
    alerts: ExecutiveAlerts
    metadata: ExecutiveMetadata
