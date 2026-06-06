"""Pydantic IO contracts for the Reporting module.

The module exposes only two top-level response shapes used internally by
the PDF / XLSX generators (``ExecutiveReportData`` and
``ReportSection``). Public contracts are the streamed ``application/pdf``
and ``application/vnd.openxmlformats-officedocument.spreadsheetml.sheet``
files themselves.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Section blocks (used by PDF / XLSX generators)
# ---------------------------------------------------------------------------
class ReportKPI(BaseModel):
    """A single executive KPI cell (label + value + optional trend)."""

    label: str
    value: str
    secondary: str | None = None
    trend: str | None = None


class ReportTable(BaseModel):
    """A generic tabular block (column headers + 2D rows)."""

    title: str
    columns: list[str]
    rows: list[list[str]]
    total_row: list[str] | None = None


class ReportSection(BaseModel):
    """A logical section of a report — used to render both PDF and XLSX."""

    title: str
    kpis: list[ReportKPI] = Field(default_factory=list)
    tables: list[ReportTable] = Field(default_factory=list)
    paragraphs: list[str] = Field(default_factory=list)
    alerts: list[str] = Field(default_factory=list)


class ReportMetadata(BaseModel):
    generated_at: datetime
    tenant_id: UUID
    tenant_name: str
    tenant_logo_url: str | None = None
    period_label: str
    currency: str = "PEN"


# ---------------------------------------------------------------------------
# Executive composite data (everything the executive report needs)
# ---------------------------------------------------------------------------
class ExecutiveReportData(BaseModel):
    """Pre-aggregated dataset the generators consume.

    The service composes this from the existing repository
    aggregations; the generators do not touch the DB themselves.
    """

    metadata: ReportMetadata
    kpis: list[ReportKPI]
    sections: list[ReportSection]
    ai_recommendations: list[dict[str, Any]] = Field(default_factory=list)
    critical_alerts: list[str] = Field(default_factory=list)
    model_config = ConfigDict(arbitrary_types_allowed=True)


# ---------------------------------------------------------------------------
# Per-section data classes (used by the service to assemble the composite)
# ---------------------------------------------------------------------------
class SalesKPIs(BaseModel):
    sales_today: Decimal
    sales_week: Decimal
    sales_month: Decimal
    sales_year: Decimal
    average_ticket: Decimal
    average_ticket_month: Decimal
    total_orders: int
    orders_today: int = 0
    orders_week: int = 0
    orders_month: int = 0


class CustomerKPIs(BaseModel):
    total: int
    active: int
    recurrent: int
    vip: int
    inactive: int
    average_lifetime_value: Decimal
    average_orders_per_customer: Decimal


class PipelineKPIs(BaseModel):
    open_deals: int
    won_deals: int
    lost_deals: int
    conversion_pct: float
    total_value: Decimal
    weighted_value: Decimal
    won_value: Decimal
    lost_value: Decimal


class InventoryKPIs(BaseModel):
    total_products: int
    out_of_stock: int
    low_stock: int
    normal_stock: int
    inventory_value: Decimal
    total_units: int
    total_reserved_units: int


class DailySalesPoint(BaseModel):
    date: str
    revenue: Decimal
    orders: int


class MonthlySalesPoint(BaseModel):
    month: str
    revenue: Decimal
    orders: int


class TopCustomerRow(BaseModel):
    full_name: str
    order_count: int
    lifetime_value: Decimal
    is_vip: bool = False


class TopProductRow(BaseModel):
    name: str
    units_sold: int
    revenue: Decimal
