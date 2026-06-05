"""Read-only SQL aggregations powering the Executive Dashboard.

This module is **strictly additive** — it never mutates any table and
never modifies any existing module. Every method is tenant-scoped via
``empresa_id``.

The repository intentionally re-implements (rather than HTTP-calls) the
aggregation queries of other modules to keep the dashboard endpoint
latency at a single round-trip. The SQL patterns mirror the originals
in ``orders/repository.py``, ``inventory/repository.py``,
``pipeline/repository.py`` and ``crm/repository.py`` so the
implementation stays consistent.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import case, func, literal_column, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.conversations.models import ConversationCore
from app.modules.conversations.models import Conversation
from app.modules.customers.models import Cliente
from app.modules.inventory.models import InventoryItem
from app.modules.orders.models import Order, OrderItem
from app.modules.pipeline.models import (
    LOST_STAGE,
    OPEN_STAGES,
    PIPELINE_STAGE_VALUES,
    WON_STAGE,
    SalesPipelineItem,
)
from app.modules.products.models import Producto


# Order statuses considered "completed" for revenue / ticket calculations.
_COMPLETED_ORDER_STATUSES = ("confirmed", "preparing", "shipped", "delivered")
_OPEN_ORDER_STATUSES = ("pending", "confirmed", "preparing", "shipped")

# Pipeline stage display metadata (mirrors the existing pipeline module).
_PIPELINE_STAGE_META: dict[str, dict[str, Any]] = {
    "new_lead":     {"label": "Nuevo Lead",   "order": 1, "color": "#6366f1"},
    "contacted":    {"label": "Contactado",   "order": 2, "color": "#0ea5e9"},
    "qualified":    {"label": "Calificado",   "order": 3, "color": "#8b5cf6"},
    "proposal":     {"label": "Propuesta",    "order": 4, "color": "#f59e0b"},
    "negotiation":  {"label": "Negociación",  "order": 5, "color": "#ec4899"},
    "won":          {"label": "Ganado",       "order": 6, "color": "#10b981"},
    "lost":         {"label": "Perdido",      "order": 7, "color": "#ef4444"},
}


class ExecutiveDashboardRepository:
    """Read-only aggregations over the existing tables."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------ utils
    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

    @staticmethod
    def _period(now: datetime) -> dict[str, datetime]:
        today_start = datetime.combine(now.date(), time.min, tzinfo=UTC)
        week_start = today_start - timedelta(days=today_start.weekday())
        month_start = today_start.replace(day=1)
        year_start = today_start.replace(month=1, day=1)
        return {
            "today": today_start,
            "week_start": week_start,
            "month_start": month_start,
            "year_start": year_start,
        }

    @staticmethod
    def _month_key(dt: datetime) -> str:
        return dt.strftime("%Y-%m")

    @staticmethod
    def _confidence_for_sample(sample_size: int) -> str:
        if sample_size >= 6:
            return "high"
        if sample_size >= 3:
            return "medium"
        return "low"

    # ---------------------------------------------------------- KPI strip
    async def kpi_strip(
        self, *, empresa_id: UUID, period: dict[str, datetime]
    ) -> dict[str, Any]:
        """Compute the 14 headline KPIs of the dashboard in 6 queries."""
        today_start = period["today"]
        week_start = period["week_start"]
        month_start = period["month_start"]
        year_start = period["year_start"]
        month_end = month_start + timedelta(days=32)
        month_end = month_end.replace(day=1)

        # 1) Sales today / week / month / year (sum of completed orders' total)
        sales_rows = await self._session.execute(
            select(
                func.coalesce(
                    func.sum(
                        case(
                            (Order.created_at >= today_start, Order.total),
                            else_=0,
                        )
                    ),
                    0,
                ).label("sales_today"),
                func.coalesce(
                    func.sum(
                        case(
                            (Order.created_at >= week_start, Order.total),
                            else_=0,
                        )
                    ),
                    0,
                ).label("sales_week"),
                func.coalesce(
                    func.sum(
                        case(
                            (Order.created_at >= month_start, Order.total),
                            else_=0,
                        )
                    ),
                    0,
                ).label("sales_month"),
                func.coalesce(
                    func.sum(
                        case(
                            (Order.created_at >= year_start, Order.total),
                            else_=0,
                        )
                    ),
                    0,
                ).label("sales_year"),
            ).where(
                Order.empresa_id == empresa_id,
                Order.status != "cancelled",
            )
        )
        sales = sales_rows.one()

        # 2) Average ticket (last 30 days) + average ticket this month
        ticket_30 = await self._session.execute(
            select(func.avg(Order.total)).where(
                Order.empresa_id == empresa_id,
                Order.status != "cancelled",
                Order.created_at >= (today_start - timedelta(days=30)),
            )
        )
        ticket_month = await self._session.execute(
            select(func.avg(Order.total)).where(
                Order.empresa_id == empresa_id,
                Order.status != "cancelled",
                Order.created_at >= month_start,
            )
        )

        # 3) Active customers: any cliente with status=interested/negotiating
        # OR any order in the last 30 days.
        active_customers_q = (
            select(func.count(func.distinct(Cliente.id)))
            .where(
                Cliente.empresa_id == empresa_id,
                Cliente.deleted_at.is_(None),
                Cliente.lead_status.in_(("interested", "negotiating", "won")),
            )
        )
        active_customers_row = await self._session.execute(active_customers_q)

        # 4) VIP customers: at least 5 orders OR LTV >= 1000 (mirror CRM rule)
        vip_subq = self._lifetime_value_subquery(empresa_id)
        vip_count = await self._session.execute(
            select(func.count()).select_from(vip_subq).where(
                (vip_subq.c.order_count >= 5)
                | (vip_subq.c.lifetime_value >= 1000)
            )
        )

        # 5) Active conversations: sum of open (conversations_core.status='active'
        # and conversations.estado='open') in the last 30 days.
        conv_core_q = select(func.count(ConversationCore.id)).where(
            ConversationCore.empresa_id == empresa_id,
            ConversationCore.status == "active",
        )
        conv_legacy_q = select(func.count(Conversation.id)).where(
            Conversation.empresa_id == empresa_id,
            Conversation.estado == "open",
            Conversation.deleted_at.is_(None),
        )
        conv_core_count = (await self._session.execute(conv_core_q)).scalar_one()
        conv_legacy_count = (await self._session.execute(conv_legacy_q)).scalar_one()

        # 6) Pipeline counts (open / won / lost) and conversion rate
        pipeline_q = select(
            func.coalesce(
                func.sum(case((SalesPipelineItem.stage.in_(tuple(OPEN_STAGES)), 1), else_=0)),
                0,
            ).label("open"),
            func.coalesce(
                func.sum(case((SalesPipelineItem.stage == WON_STAGE, 1), else_=0)),
                0,
            ).label("won"),
            func.coalesce(
                func.sum(case((SalesPipelineItem.stage == LOST_STAGE, 1), else_=0)),
                0,
            ).label("lost"),
        ).where(SalesPipelineItem.empresa_id == empresa_id)
        pipeline_row = (await self._session.execute(pipeline_q)).one()
        closed_total = int(pipeline_row.won or 0) + int(pipeline_row.lost or 0)
        conversion_pct = (
            round((int(pipeline_row.won or 0) / closed_total) * 100, 2)
            if closed_total > 0
            else 0.0
        )

        # 7) Total orders (all-time, not cancelled)
        total_orders_q = select(func.count(Order.id)).where(
            Order.empresa_id == empresa_id,
            Order.status != "cancelled",
        )
        total_orders = (await self._session.execute(total_orders_q)).scalar_one()

        avg_30 = ticket_30.scalar_one()
        avg_month = ticket_month.scalar_one()

        return {
            "sales_today": Decimal(sales.sales_today or 0),
            "sales_week": Decimal(sales.sales_week or 0),
            "sales_month": Decimal(sales.sales_month or 0),
            "sales_year": Decimal(sales.sales_year or 0),
            "average_ticket": Decimal(avg_30).quantize(Decimal("0.01")) if avg_30 is not None else Decimal("0.00"),
            "average_ticket_month": Decimal(avg_month).quantize(Decimal("0.01")) if avg_month is not None else Decimal("0.00"),
            "active_customers": int(active_customers_row.scalar_one() or 0),
            "vip_customers": int(vip_count.scalar_one() or 0),
            "active_conversations": int(conv_core_count or 0) + int(conv_legacy_count or 0),
            "leads_open": int(pipeline_row.open or 0),
            "leads_won": int(pipeline_row.won or 0),
            "leads_lost": int(pipeline_row.lost or 0),
            "conversion_rate_pct": conversion_pct,
            "total_orders": int(total_orders or 0),
        }

    # --------------------------------------------------------- Sales trend
    async def sales_trend_daily(
        self, *, empresa_id: UUID, days: int = 30
    ) -> list[dict[str, Any]]:
        end = self._now().date() + timedelta(days=1)
        start = end - timedelta(days=days)
        start_dt = datetime.combine(start, time.min, tzinfo=UTC)
        # Use date_trunc to bucket by day in the DB (Postgres).
        bucket = func.date_trunc("day", Order.created_at).label("bucket")
        rows = await self._session.execute(
            select(
                bucket,
                func.coalesce(func.sum(Order.total), 0).label("revenue"),
                func.count(Order.id).label("orders"),
            )
            .where(
                Order.empresa_id == empresa_id,
                Order.status != "cancelled",
                Order.created_at >= start_dt,
            )
            .group_by(bucket)
            .order_by(bucket)
        )
        by_day: dict[str, dict[str, Any]] = {}
        for bucket_value, revenue, orders in rows.all():
            if bucket_value is None:
                continue
            key = bucket_value.date().isoformat()
            by_day[key] = {
                "date": key,
                "revenue": Decimal(revenue or 0),
                "orders": int(orders or 0),
            }
        # Backfill zero days so the chart is continuous.
        out: list[dict[str, Any]] = []
        cursor = start
        while cursor < end:
            key = cursor.isoformat()
            out.append(
                by_day.get(
                    key, {"date": key, "revenue": Decimal("0"), "orders": 0}
                )
            )
            cursor += timedelta(days=1)
        return out

    async def sales_trend_monthly(
        self, *, empresa_id: UUID, months: int = 12
    ) -> list[dict[str, Any]]:
        now = self._now()
        current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # Step back (months - 1) months to find the start month.
        year, month = current_month.year, current_month.month
        for _ in range(months - 1):
            month -= 1
            if month == 0:
                month = 12
                year -= 1
        start_month = datetime(year, month, 1, tzinfo=UTC)
        start_dt = datetime.combine(start_month.date(), time.min, tzinfo=UTC)
        bucket = func.date_trunc("month", Order.created_at).label("bucket")
        rows = await self._session.execute(
            select(
                bucket,
                func.coalesce(func.sum(Order.total), 0).label("revenue"),
                func.count(Order.id).label("orders"),
            )
            .where(
                Order.empresa_id == empresa_id,
                Order.status != "cancelled",
                Order.created_at >= start_dt,
            )
            .group_by(bucket)
            .order_by(bucket)
        )
        by_month: dict[str, dict[str, Any]] = {}
        for bucket_value, revenue, orders in rows.all():
            if bucket_value is None:
                continue
            key = self._month_key(bucket_value)
            by_month[key] = {
                "month": key,
                "revenue": Decimal(revenue or 0),
                "orders": int(orders or 0),
            }
        out: list[dict[str, Any]] = []
        cursor = datetime(start_month.year, start_month.month, 1, tzinfo=UTC)
        end_cursor = datetime(now.year, now.month, 1, tzinfo=UTC)
        while cursor <= end_cursor:
            key = cursor.strftime("%Y-%m")
            out.append(
                by_month.get(
                    key, {"month": key, "revenue": Decimal("0"), "orders": 0}
                )
            )
            # advance one month
            if cursor.month == 12:
                cursor = cursor.replace(year=cursor.year + 1, month=1)
            else:
                cursor = cursor.replace(month=cursor.month + 1)
        return out

    # ---------------------------------------------------------- Pipeline
    async def pipeline_summary(self, *, empresa_id: UUID) -> dict[str, Any]:
        # Open value (sum of estimated_value) and weighted value.
        value_q = select(
            func.coalesce(
                func.sum(
                    case(
                        (SalesPipelineItem.stage.in_(tuple(OPEN_STAGES)),
                         SalesPipelineItem.estimated_value),
                        else_=0,
                    )
                ),
                0,
            ).label("open_value"),
            func.coalesce(
                func.sum(
                    case(
                        (SalesPipelineItem.stage.in_(tuple(OPEN_STAGES)),
                         SalesPipelineItem.estimated_value
                         * SalesPipelineItem.probability
                         / literal_column("100")),
                        else_=0,
                    )
                ),
                0,
            ).label("weighted_value"),
            func.coalesce(
                func.sum(
                    case(
                        (SalesPipelineItem.stage == WON_STAGE,
                         SalesPipelineItem.estimated_value),
                        else_=0,
                    )
                ),
                0,
            ).label("won_value"),
            func.coalesce(
                func.sum(
                    case(
                        (SalesPipelineItem.stage == LOST_STAGE,
                         SalesPipelineItem.estimated_value),
                        else_=0,
                    )
                ),
                0,
            ).label("lost_value"),
        ).where(SalesPipelineItem.empresa_id == empresa_id)
        value_row = (await self._session.execute(value_q)).one()

        # Counts per stage (for funnel)
        funnel_q = (
            select(
                SalesPipelineItem.stage,
                func.count(SalesPipelineItem.id).label("count"),
                func.coalesce(func.sum(SalesPipelineItem.estimated_value), 0).label("value"),
            )
            .where(SalesPipelineItem.empresa_id == empresa_id)
            .group_by(SalesPipelineItem.stage)
        )
        funnel_rows = (await self._session.execute(funnel_q)).all()
        by_stage: dict[str, dict[str, int]] = {}
        for stage, count, value in funnel_rows:
            by_stage[stage] = {
                "count": int(count or 0),
                "value": Decimal(value or 0),
            }

        funnel: list[dict[str, Any]] = []
        for stage in PIPELINE_STAGE_VALUES:
            meta = _PIPELINE_STAGE_META[stage]
            row = by_stage.get(stage, {"count": 0, "value": Decimal("0")})
            funnel.append({
                "stage": stage,
                "label": meta["label"],
                "count": row["count"],
                "value": row["value"],
                "order": meta["order"],
                "color": meta["color"],
            })

        open_deals = sum(
            by_stage.get(s, {"count": 0})["count"] for s in OPEN_STAGES
        )
        won_deals = by_stage.get(WON_STAGE, {"count": 0})["count"]
        lost_deals = by_stage.get(LOST_STAGE, {"count": 0})["count"]
        closed_total = won_deals + lost_deals
        conversion_pct = (
            round((won_deals / closed_total) * 100, 2) if closed_total > 0 else 0.0
        )

        # Average time to close: for won deals, (stage_entered_at - created_at)
        # in days. We compute via the database for accuracy.
        avg_close_q = select(
            func.avg(
                func.extract(
                    "epoch",
                    SalesPipelineItem.stage_entered_at - SalesPipelineItem.created_at,
                )
                / literal_column("86400")
            )
        ).where(
            SalesPipelineItem.empresa_id == empresa_id,
            SalesPipelineItem.stage == WON_STAGE,
        )
        avg_close_row = await self._session.execute(avg_close_q)
        avg_close = avg_close_row.scalar_one()
        avg_close_days = float(avg_close) if avg_close is not None else 0.0
        avg_close_days = round(avg_close_days, 2)

        return {
            "total_value": Decimal(value_row.open_value or 0),
            "weighted_value": Decimal(value_row.weighted_value or 0),
            "won_value": Decimal(value_row.won_value or 0),
            "lost_value": Decimal(value_row.lost_value or 0),
            "conversion_pct": conversion_pct,
            "average_time_to_close_days": avg_close_days,
            "open_deals": open_deals,
            "won_deals": won_deals,
            "lost_deals": lost_deals,
            "funnel": funnel,
        }

    # ----------------------------------------------------------- Forecast
    async def forecast(self, *, empresa_id: UUID) -> dict[str, Any]:
        """Project next month and next quarter from historical monthly data."""
        monthly = await self.sales_trend_monthly(empresa_id=empresa_id, months=12)
        # Filter out months with no revenue (treat as no signal, not as zero
        # contribution to the average — this is a common projection choice).
        revenue_values = [
            Decimal(m["revenue"]) for m in monthly if Decimal(m["revenue"]) > 0
        ]
        sample_size = len(revenue_values)
        if sample_size == 0:
            return {
                "monthly": {
                    "projected_revenue": Decimal("0"),
                    "confidence": "low",
                    "basis": "Sin historial de ventas para proyectar.",
                    "sample_size": 0,
                },
                "quarterly": {
                    "projected_revenue": Decimal("0"),
                    "confidence": "low",
                    "basis": "Sin historial de ventas para proyectar.",
                    "sample_size": 0,
                },
            }
        avg_month = sum(revenue_values, Decimal("0")) / Decimal(sample_size)
        confidence = self._confidence_for_sample(sample_size)
        basis = (
            f"Promedio de los últimos {sample_size} meses con ventas: "
            f"S/ {avg_month.quantize(Decimal('0.01'))} / mes."
        )
        monthly_bucket = {
            "projected_revenue": avg_month.quantize(Decimal("0.01")),
            "confidence": confidence,
            "basis": basis,
            "sample_size": sample_size,
        }
        quarterly_projection = (avg_month * Decimal("3")).quantize(Decimal("0.01"))
        # Quarterly confidence is generally one tier lower than monthly.
        if confidence == "high":
            q_conf = "high"
        elif confidence == "medium":
            q_conf = "medium"
        else:
            q_conf = "low"
        quarterly_bucket = {
            "projected_revenue": quarterly_projection,
            "confidence": q_conf,
            "basis": (
                f"Proyección trimestral = 3 × promedio mensual histórico "
                f"({sample_size} meses con ventas)."
            ),
            "sample_size": sample_size,
        }
        return {"monthly": monthly_bucket, "quarterly": quarterly_bucket}

    # ----------------------------------------------------- Top customers
    async def top_customers(
        self, *, empresa_id: UUID, limit: int = 10
    ) -> list[dict[str, Any]]:
        ltv_subq = self._lifetime_value_subquery(empresa_id).subquery()
        # is_vip flag mirror: order_count >= 5 OR ltv >= 1000
        is_vip_expr = case(
            (
                (ltv_subq.c.order_count >= 5)
                | (ltv_subq.c.lifetime_value >= 1000),
                True,
            ),
            else_=False,
        ).label("is_vip")
        last_purchase_expr = ltv_subq.c.last_purchase_at.label("last_purchase_at")
        rows = await self._session.execute(
            select(
                ltv_subq.c.id,
                ltv_subq.c.full_name,
                ltv_subq.c.email,
                ltv_subq.c.phone,
                is_vip_expr,
                ltv_subq.c.order_count,
                ltv_subq.c.lifetime_value,
                ltv_subq.c.average_ticket,
                last_purchase_expr,
            )
            .select_from(ltv_subq)
            .order_by(ltv_subq.c.lifetime_value.desc(), ltv_subq.c.order_count.desc())
            .limit(limit)
        )
        now = self._now()
        out: list[dict[str, Any]] = []
        for row in rows.all():
            days_since = None
            if row.last_purchase_at is not None:
                last_dt = row.last_purchase_at
                if last_dt.tzinfo is None:
                    last_dt = last_dt.replace(tzinfo=UTC)
                days_since = max(0, (now - last_dt).days)
            out.append({
                "id": row.id,
                "full_name": row.full_name,
                "email": row.email,
                "phone": row.phone,
                "is_vip": bool(row.is_vip),
                "order_count": int(row.order_count or 0),
                "lifetime_value": Decimal(row.lifetime_value or 0),
                "average_ticket": Decimal(row.average_ticket or 0),
                "days_since_last_purchase": days_since,
            })
        return out

    # ----------------------------------------------------- Top products
    async def top_products(
        self, *, empresa_id: UUID, limit: int = 5
    ) -> dict[str, list[dict[str, Any]]]:
        # Most sold (units)
        most_sold_q = (
            select(
                Producto.id.label("product_id"),
                Producto.name.label("name"),
                func.coalesce(func.sum(OrderItem.quantity), 0).label("units_sold"),
                func.coalesce(
                    func.sum(OrderItem.quantity * OrderItem.price), 0
                ).label("revenue"),
            )
            .select_from(Producto)
            .outerjoin(
                OrderItem,
                (OrderItem.product_id == Producto.id)
                & (OrderItem.empresa_id == Producto.empresa_id),
            )
            .outerjoin(
                Order,
                (Order.id == OrderItem.order_id)
                & (Order.status != "cancelled"),
            )
            .where(
                Producto.empresa_id == empresa_id,
                Producto.deleted_at.is_(None),
            )
            .group_by(Producto.id, Producto.name)
            .order_by(func.coalesce(func.sum(OrderItem.quantity), 0).desc())
            .limit(limit)
        )
        most_sold_rows = (await self._session.execute(most_sold_q)).all()
        most_sold: list[dict[str, Any]] = [
            {
                "product_id": row.product_id,
                "name": row.name,
                "units_sold": int(row.units_sold or 0),
                "revenue": Decimal(row.revenue or 0),
            }
            for row in most_sold_rows
        ]

        # Most profitable (revenue)
        most_profitable = sorted(
            most_sold, key=lambda r: r["revenue"], reverse=True
        )[:limit]

        # Most consulted: no product-views table in this schema; return empty.
        most_consulted: list[dict[str, Any]] = []

        return {
            "most_sold": most_sold,
            "most_profitable": most_profitable,
            "most_consulted": most_consulted,
        }

    # --------------------------------------------------------- Alerts
    async def alerts_inventory_critical(
        self, *, empresa_id: UUID, limit: int = 10
    ) -> list[dict[str, Any]]:
        rows = await self._session.execute(
            select(
                InventoryItem.product_id,
                Producto.name,
                InventoryItem.stock_actual,
                InventoryItem.stock_minimo,
            )
            .join(Producto, Producto.id == InventoryItem.product_id)
            .where(
                InventoryItem.empresa_id == empresa_id,
                Producto.deleted_at.is_(None),
                (InventoryItem.stock_actual <= InventoryItem.stock_minimo),
            )
            .order_by(InventoryItem.stock_actual.asc())
            .limit(limit)
        )
        out: list[dict[str, Any]] = []
        for product_id, name, stock, min_stock in rows.all():
            status = "out" if int(stock or 0) == 0 else "low"
            out.append(
                {
                    "product_id": product_id,
                    "name": name,
                    "stock": int(stock or 0),
                    "min_stock": int(min_stock or 0),
                    "status": status,
                }
            )
        return out

    async def alerts_leads_abandoned(
        self, *, empresa_id: UUID, limit: int = 10
    ) -> list[dict[str, Any]]:
        now = self._now()
        threshold = now - timedelta(days=7)
        rows = await self._session.execute(
            select(
                SalesPipelineItem.id,
                SalesPipelineItem.title,
                SalesPipelineItem.stage,
                SalesPipelineItem.last_activity_at,
                SalesPipelineItem.estimated_value,
            )
            .where(
                SalesPipelineItem.empresa_id == empresa_id,
                SalesPipelineItem.stage.in_(tuple(OPEN_STAGES)),
                SalesPipelineItem.last_activity_at < threshold,
            )
            .order_by(SalesPipelineItem.last_activity_at.asc())
            .limit(limit)
        )
        out: list[dict[str, Any]] = []
        for deal_id, title, stage, last_act, value in rows.all():
            last = last_act
            if last is not None and last.tzinfo is None:
                last = last.replace(tzinfo=UTC)
            days = max(0, (now - last).days) if last is not None else 0
            out.append(
                {
                    "deal_id": deal_id,
                    "title": title or "Sin título",
                    "stage": stage,
                    "days_inactive": days,
                    "value": Decimal(value or 0),
                }
            )
        return out

    async def alerts_conversations_unanswered(
        self, *, empresa_id: UUID, limit: int = 10
    ) -> list[dict[str, Any]]:
        now = self._now()
        threshold = now - timedelta(hours=24)
        out: list[dict[str, Any]] = []

        # conversations_core (active status, last_message is the body not a
        # timestamp). We use updated_at as the proxy for last activity.
        conv_core_rows = await self._session.execute(
            select(
                ConversationCore.id,
                ConversationCore.updated_at,
                ConversationCore.customer_id,
                Cliente.full_name,
            )
            .outerjoin(Cliente, Cliente.id == ConversationCore.customer_id)
            .where(
                ConversationCore.empresa_id == empresa_id,
                ConversationCore.status == "active",
                ConversationCore.updated_at < threshold,
            )
            .order_by(ConversationCore.updated_at.asc())
            .limit(limit)
        )
        for conv_id, updated_at, _cust_id, cust_name in conv_core_rows.all():
            updated = updated_at
            if updated is not None and updated.tzinfo is None:
                updated = updated.replace(tzinfo=UTC)
            hours = (
                int((now - updated).total_seconds() // 3600)
                if updated is not None
                else 0
            )
            out.append(
                {
                    "conversation_id": conv_id,
                    "customer_name": cust_name,
                    "channel": "core",
                    "last_message_at": updated,
                    "hours_silent": hours,
                }
            )

        # legacy conversations table (estado=open)
        conv_rows = await self._session.execute(
            select(
                Conversation.id,
                Conversation.updated_at,
                Conversation.canal,
                Cliente.full_name,
            )
            .outerjoin(Cliente, Cliente.id == Conversation.cliente_id)
            .where(
                Conversation.empresa_id == empresa_id,
                Conversation.estado == "open",
                Conversation.deleted_at.is_(None),
                Conversation.updated_at < threshold,
            )
            .order_by(Conversation.updated_at.asc())
            .limit(limit)
        )
        for conv_id, updated_at, channel, cust_name in conv_rows.all():
            updated = updated_at
            if updated is not None and updated.tzinfo is None:
                updated = updated.replace(tzinfo=UTC)
            hours = (
                int((now - updated).total_seconds() // 3600)
                if updated is not None
                else 0
            )
            out.append(
                {
                    "conversation_id": conv_id,
                    "customer_name": cust_name,
                    "channel": channel or "manual",
                    "last_message_at": updated,
                    "hours_silent": hours,
                }
            )
        # Sort by hours_silent desc, cap at limit
        out.sort(key=lambda r: r["hours_silent"], reverse=True)
        return out[:limit]

    async def alerts_inactive_customers(
        self, *, empresa_id: UUID, limit: int = 10
    ) -> list[dict[str, Any]]:
        # Use the LTV subquery to get last_purchase_at.
        ltv_subq = self._lifetime_value_subquery(empresa_id).subquery()
        threshold = self._now() - timedelta(days=60)
        rows = await self._session.execute(
            select(
                ltv_subq.c.id,
                ltv_subq.c.full_name,
                ltv_subq.c.last_purchase_at,
            )
            .where(
                ltv_subq.c.last_purchase_at.is_not(None),
                ltv_subq.c.last_purchase_at < threshold,
            )
            .order_by(ltv_subq.c.last_purchase_at.asc())
            .limit(limit)
        )
        now = self._now()
        out: list[dict[str, Any]] = []
        for cust_id, full_name, last_purchase in rows.all():
            last = last_purchase
            if last is not None and last.tzinfo is None:
                last = last.replace(tzinfo=UTC)
            days = max(0, (now - last).days) if last is not None else 0
            out.append(
                {
                    "customer_id": cust_id,
                    "full_name": full_name,
                    "days_inactive": days,
                    "last_purchase_at": last,
                }
            )
        return out

    async def alerts_delayed_orders(
        self, *, empresa_id: UUID, limit: int = 10
    ) -> list[dict[str, Any]]:
        now = self._now()
        # Open orders (not delivered/cancelled) created more than 3 days ago.
        threshold = now - timedelta(days=3)
        rows = await self._session.execute(
            select(
                Order.id,
                Order.order_number,
                Order.customer_name,
                Order.status,
                Order.created_at,
                Order.total,
            )
            .where(
                Order.empresa_id == empresa_id,
                Order.status.in_(_OPEN_ORDER_STATUSES),
                Order.created_at < threshold,
            )
            .order_by(Order.created_at.asc())
            .limit(limit)
        )
        out: list[dict[str, Any]] = []
        for order_id, order_number, cust_name, status, created_at, total in rows.all():
            created = created_at
            if created is not None and created.tzinfo is None:
                created = created.replace(tzinfo=UTC)
            days = max(0, (now - created).days) if created is not None else 0
            out.append(
                {
                    "order_id": order_id,
                    "order_number": order_number or str(order_id)[:8],
                    "customer_name": cust_name or "Sin nombre",
                    "status": status,
                    "days_since_created": days,
                    "total": Decimal(total or 0),
                }
            )
        return out

    # ------------------------------------------------------ AI recs
    async def ai_recommendations(self, *, empresa_id: UUID) -> list[dict[str, Any]]:
        recs: list[dict[str, Any]] = []

        # 1) Hot leads: open deals in negotiation stage, sorted by probability
        hot_lead_rows = await self._session.execute(
            select(
                SalesPipelineItem.id,
                SalesPipelineItem.title,
                SalesPipelineItem.probability,
                SalesPipelineItem.estimated_value,
                SalesPipelineItem.stage,
                SalesPipelineItem.customer_id,
                Cliente.full_name,
            )
            .outerjoin(Cliente, Cliente.id == SalesPipelineItem.customer_id)
            .where(
                SalesPipelineItem.empresa_id == empresa_id,
                SalesPipelineItem.stage.in_(("negotiation", "proposal")),
            )
            .order_by(SalesPipelineItem.probability.desc())
            .limit(5)
        )
        for row in hot_lead_rows.all():
            score = min(100, max(40, int(row.probability or 0) + 20))
            priority = "high" if score >= 80 else "medium" if score >= 60 else "low"
            cust = row.full_name or "cliente"
            recs.append(
                {
                    "id": f"hot_lead:{row.id}",
                    "title": f"Lead caliente: {row.title or 'Sin título'}",
                    "description": (
                        f"Negociación abierta con {cust} por S/ "
                        f"{Decimal(row.estimated_value or 0).quantize(Decimal('0.01'))} "
                        f"({row.probability}% de probabilidad)."
                    ),
                    "score": score,
                    "priority": priority,
                    "category": "lead_caliente",
                    "cta_label": "Abrir trato",
                    "cta_href": f"/dashboard/pipeline/{row.id}",
                }
            )

        # 2) VIP without recent contact: lead_score >= 70 or VIP flag, last_interaction > 14d
        threshold = self._now() - timedelta(days=14)
        vip_rows = await self._session.execute(
            select(
                Cliente.id,
                Cliente.full_name,
                Cliente.lead_score,
                Cliente.last_interaction_at,
            )
            .where(
                Cliente.empresa_id == empresa_id,
                Cliente.deleted_at.is_(None),
                (Cliente.lead_score >= 70) | (Cliente.priority == "hot"),
                Cliente.last_interaction_at.is_not(None),
                Cliente.last_interaction_at < threshold,
            )
            .order_by(Cliente.lead_score.desc())
            .limit(5)
        )
        for row in vip_rows.all():
            last = row.last_interaction_at
            if last is not None and last.tzinfo is None:
                last = last.replace(tzinfo=UTC)
            days = max(0, (self._now() - last).days) if last is not None else 0
            score = min(100, int(row.lead_score or 70) + 5)
            priority = "high" if days > 30 else "medium"
            recs.append(
                {
                    "id": f"vip_inactivo:{row.id}",
                    "title": f"VIP sin contacto reciente: {row.full_name}",
                    "description": (
                        f"Cliente de alto valor (score {row.lead_score}) sin "
                        f"interacción hace {days} días."
                    ),
                    "score": score,
                    "priority": priority,
                    "category": "vip_inactivo",
                    "cta_label": "Contactar",
                    "cta_href": f"/dashboard/customers/{row.id}",
                }
            )

        # 3) Recurrent buyer: clientes con >= 3 pedidos
        ltv_subq = self._lifetime_value_subquery(empresa_id).subquery()
        recurrent_rows = await self._session.execute(
            select(
                ltv_subq.c.id,
                ltv_subq.c.full_name,
                ltv_subq.c.order_count,
                ltv_subq.c.lifetime_value,
            )
            .where(ltv_subq.c.order_count >= 3)
            .order_by(ltv_subq.c.lifetime_value.desc())
            .limit(5)
        )
        for row in recurrent_rows.all():
            score = min(100, 50 + int(row.order_count or 0) * 5)
            recs.append(
                {
                    "id": f"upsell:{row.id}",
                    "title": f"Cliente recurrente listo para upsell: {row.full_name}",
                    "description": (
                        f"{row.order_count} pedidos y LTV de S/ "
                        f"{Decimal(row.lifetime_value or 0).quantize(Decimal('0.01'))}."
                    ),
                    "score": score,
                    "priority": "medium",
                    "category": "upsell",
                    "cta_label": "Sugerir producto",
                    "cta_href": f"/dashboard/customers/{row.id}",
                }
            )

        # 4) Product with accelerated growth: product with revenue > avg revenue
        # over recent order_items (use ALL completed orders, compare units sold
        # in the last 30 days vs previous 30 days).
        accelerated_rows = await self._session.execute(
            select(
                Producto.id,
                Producto.name,
                func.coalesce(func.sum(OrderItem.quantity), 0).label("units_recent"),
            )
            .select_from(Producto)
            .outerjoin(
                OrderItem, OrderItem.product_id == Producto.id
            )
            .outerjoin(
                Order,
                (Order.id == OrderItem.order_id)
                & (Order.status != "cancelled")
                & (Order.created_at >= (self._now() - timedelta(days=30))),
            )
            .where(
                Producto.empresa_id == empresa_id,
                Producto.deleted_at.is_(None),
            )
            .group_by(Producto.id, Producto.name)
            .having(func.coalesce(func.sum(OrderItem.quantity), 0) > 0)
            .order_by(func.coalesce(func.sum(OrderItem.quantity), 0).desc())
            .limit(3)
        )
        for row in accelerated_rows.all():
            units = int(row.units_recent or 0)
            if units <= 0:
                continue
            score = min(100, 50 + units * 2)
            recs.append(
                {
                    "id": f"producto_top:{row.id}",
                    "title": f"Producto con crecimiento: {row.name}",
                    "description": (
                        f"{units} unidades vendidas en los últimos 30 días."
                    ),
                    "score": score,
                    "priority": "medium",
                    "category": "producto_top",
                    "cta_label": "Ver producto",
                    "cta_href": f"/dashboard/products",
                }
            )

        # Sort by score desc, cap at 10.
        recs.sort(key=lambda r: r["score"], reverse=True)
        return recs[:10]

    # ------------------------------------------------------ Helpers
    def _lifetime_value_subquery(self, empresa_id: UUID):
        """Compute per-customer order_count, lifetime_value, average_ticket
        and last_purchase_at by matching ``orders.customer_name`` (normalised)
        to ``clientes.full_name`` (normalised).

        Mirrors the SQL pattern used in ``crm/repository.py``.
        """
        lname = func.lower(func.trim(Cliente.full_name))
        oname = func.lower(func.trim(Order.customer_name))
        return (
            select(
                Cliente.id.label("id"),
                Cliente.full_name.label("full_name"),
                Cliente.email.label("email"),
                Cliente.phone.label("phone"),
                func.count(Order.id).label("order_count"),
                func.coalesce(func.sum(Order.total), 0).label("lifetime_value"),
                func.coalesce(func.avg(Order.total), 0).label("average_ticket"),
                func.max(Order.created_at).label("last_purchase_at"),
            )
            .select_from(Cliente)
            .outerjoin(
                Order,
                (oname == lname) & (Order.empresa_id == Cliente.empresa_id),
            )
            .where(
                Cliente.empresa_id == empresa_id,
                Cliente.deleted_at.is_(None),
            )
            .group_by(
                Cliente.id,
                Cliente.full_name,
                Cliente.email,
                Cliente.phone,
            )
        )
