"""Orchestration for the executive dashboard.

The service composes the read-only repository calls into the single
``ExecutiveDashboardResponse`` payload consumed by the frontend.

No write paths — read-only and idempotent.
"""
from __future__ import annotations

import time
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.executive_dashboard.repository import ExecutiveDashboardRepository
from app.modules.executive_dashboard.schemas import (
    ExecutiveAlerts,
    ExecutiveDashboardResponse,
    ExecutiveForecast,
    ExecutiveKPIStrip,
    ExecutiveMetadata,
    ExecutivePeriod,
    ExecutivePipelineSummary,
    SalesTrend,
    TopCustomer,
    TopProducts,
)


class ExecutiveDashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = ExecutiveDashboardRepository(session)

    async def get_dashboard(self, *, tenant_id: UUID) -> ExecutiveDashboardResponse:
        started = time.perf_counter()
        repo = self._repo
        now = repo._now()
        period = repo._period(now)

        # Fan out the read-only aggregations. SQLAlchemy session.execute is
        # safe to call sequentially on a single AsyncSession for SELECTs.
        kpis = await repo.kpi_strip(empresa_id=tenant_id, period=period)
        daily = await repo.sales_trend_daily(empresa_id=tenant_id, days=30)
        monthly = await repo.sales_trend_monthly(empresa_id=tenant_id, months=12)
        pipeline = await repo.pipeline_summary(empresa_id=tenant_id)
        forecast = await repo.forecast(empresa_id=tenant_id)
        top_customers = await repo.top_customers(empresa_id=tenant_id, limit=10)
        top_products = await repo.top_products(empresa_id=tenant_id, limit=5)
        ai_recs = await repo.ai_recommendations(empresa_id=tenant_id)

        inv_alerts = await repo.alerts_inventory_critical(empresa_id=tenant_id)
        lead_alerts = await repo.alerts_leads_abandoned(empresa_id=tenant_id)
        conv_alerts = await repo.alerts_conversations_unanswered(
            empresa_id=tenant_id
        )
        inactive_alerts = await repo.alerts_inactive_customers(
            empresa_id=tenant_id
        )
        delayed_alerts = await repo.alerts_delayed_orders(empresa_id=tenant_id)

        elapsed_ms = int((time.perf_counter() - started) * 1000)

        return ExecutiveDashboardResponse(
            generated_at=now,
            period=ExecutivePeriod(
                today=period["today"],
                week_start=period["week_start"],
                month_start=period["month_start"],
                year_start=period["year_start"],
            ),
            currency="PEN",
            kpis=ExecutiveKPIStrip(**kpis),
            sales_trend=SalesTrend(daily=daily, monthly=monthly),
            pipeline=ExecutivePipelineSummary(**pipeline),
            ai_recommendations=ai_recs,
            forecast=ExecutiveForecast(**forecast),
            top_customers=[
                TopCustomer(
                    id=row["id"],
                    full_name=row["full_name"],
                    email=row.get("email"),
                    phone=row.get("phone"),
                    is_vip=row["is_vip"],
                    order_count=row["order_count"],
                    lifetime_value=row["lifetime_value"],
                    average_ticket=row["average_ticket"],
                    days_since_last_purchase=row.get("days_since_last_purchase"),
                )
                for row in top_customers
            ],
            top_products=TopProducts(**top_products),
            alerts=ExecutiveAlerts(
                inventory_critical=inv_alerts,
                leads_abandoned=lead_alerts,
                conversations_unanswered=conv_alerts,
                inactive_customers=inactive_alerts,
                delayed_orders=delayed_alerts,
            ),
            metadata=ExecutiveMetadata(
                tenant_id=tenant_id,
                computed_in_ms=elapsed_ms,
            ),
        )


__all__ = ["ExecutiveDashboardService"]
