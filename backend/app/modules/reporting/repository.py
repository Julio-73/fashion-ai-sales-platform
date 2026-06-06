"""Read-only aggregations powering the Reporting module.

This module is **strictly additive** — it never mutates any table and
never modifies any existing module. Every method is tenant-scoped via
``empresa_id``.

The repository intentionally re-uses the same SQL patterns as
``executive_dashboard/repository.py`` and ``crm/repository.py`` so the
implementation stays consistent with the rest of the codebase. The
report data is computed in a single pass per report (no N+1 issues).
"""
from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import case, func, literal_column, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.companies.models import Empresa
from app.modules.customers.models import Cliente
from app.modules.inventory.models import InventoryItem
from app.modules.orders.models import Order, OrderItem
from app.modules.pipeline.models import (
    LOST_STAGE,
    OPEN_STAGES,
    SalesPipelineItem,
    WON_STAGE,
)
from app.modules.products.models import Producto

_COMPLETED_ORDER_STATUSES = (
    "confirmed",
    "preparing",
    "shipped",
    "delivered",
)
_OPEN_ORDER_STATUSES = ("pending", "confirmed", "preparing", "shipped")
_INACTIVE_DAYS = 90
_INACTIVE_CUTOFF_TIMEDELTA = timedelta(days=_INACTIVE_DAYS)
_VIP_MIN_ORDERS = 5
_VIP_MIN_LIFETIME_VALUE = Decimal("1000")
_RECURRENT_MIN_ORDERS = 3


class ReportingRepository:
    """Read-only aggregations over the existing tables for the reports."""

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

    # ------------------------------------------------------------------ tenant
    async def get_empresa(self, *, empresa_id: UUID) -> dict[str, Any] | None:
        row = await self._session.execute(
            select(Empresa).where(Empresa.id == empresa_id)
        )
        emp = row.scalar_one_or_none()
        if emp is None:
            return None
        return {
            "id": emp.id,
            "nombre": emp.nombre,
            "logo_url": emp.logo_url,
        }

    # ------------------------------------------------------------------ sales
    async def sales_kpis(
        self, *, empresa_id: UUID, period: dict[str, datetime]
    ) -> dict[str, Any]:
        today_start = period["today"]
        week_start = period["week_start"]
        month_start = period["month_start"]
        year_start = period["year_start"]

        sales_row = await self._session.execute(
            select(
                func.coalesce(
                    func.sum(
                        case(
                            (Order.created_at >= today_start, Order.total), else_=0
                        )
                    ),
                    0,
                ).label("sales_today"),
                func.coalesce(
                    func.sum(
                        case(
                            (Order.created_at >= week_start, Order.total), else_=0
                        )
                    ),
                    0,
                ).label("sales_week"),
                func.coalesce(
                    func.sum(
                        case(
                            (Order.created_at >= month_start, Order.total), else_=0
                        )
                    ),
                    0,
                ).label("sales_month"),
                func.coalesce(
                    func.sum(
                        case(
                            (Order.created_at >= year_start, Order.total), else_=0
                        )
                    ),
                    0,
                ).label("sales_year"),
                func.count(case((Order.created_at >= today_start, Order.id))).label(
                    "orders_today"
                ),
                func.count(case((Order.created_at >= week_start, Order.id))).label(
                    "orders_week"
                ),
                func.count(case((Order.created_at >= month_start, Order.id))).label(
                    "orders_month"
                ),
                func.count(Order.id).label("total_orders"),
            ).where(
                Order.empresa_id == empresa_id,
                Order.status != "cancelled",
            )
        )
        sales = sales_row.one()

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
        avg_30 = ticket_30.scalar_one()
        avg_month = ticket_month.scalar_one()
        return {
            "sales_today": Decimal(sales.sales_today or 0),
            "sales_week": Decimal(sales.sales_week or 0),
            "sales_month": Decimal(sales.sales_month or 0),
            "sales_year": Decimal(sales.sales_year or 0),
            "average_ticket": (
                Decimal(avg_30).quantize(Decimal("0.01"))
                if avg_30 is not None
                else Decimal("0.00")
            ),
            "average_ticket_month": (
                Decimal(avg_month).quantize(Decimal("0.01"))
                if avg_month is not None
                else Decimal("0.00")
            ),
            "total_orders": int(sales.total_orders or 0),
            "orders_today": int(sales.orders_today or 0),
            "orders_week": int(sales.orders_week or 0),
            "orders_month": int(sales.orders_month or 0),
        }

    async def daily_sales(
        self, *, empresa_id: UUID, days: int = 30
    ) -> list[dict[str, Any]]:
        end = self._now().date() + timedelta(days=1)
        start = end - timedelta(days=days)
        start_dt = datetime.combine(start, time.min, tzinfo=UTC)
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

    async def monthly_sales(
        self, *, empresa_id: UUID, months: int = 12
    ) -> list[dict[str, Any]]:
        now = self._now()
        start_dt = now - timedelta(days=months * 31)
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
        return [
            {
                "month": self._month_key(bucket_value),
                "revenue": Decimal(revenue or 0),
                "orders": int(orders or 0),
            }
            for bucket_value, revenue, orders in rows.all()
            if bucket_value is not None
        ]

    async def orders_for_export(
        self, *, empresa_id: UUID, limit: int = 5000
    ) -> list[dict[str, Any]]:
        rows = await self._session.execute(
            select(Order)
            .where(
                Order.empresa_id == empresa_id,
            )
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        out: list[dict[str, Any]] = []
        for order in rows.scalars().all():
            out.append(
                {
                    "order_number": order.order_number or str(order.id)[:8],
                    "customer_name": order.customer_name or "Sin nombre",
                    "status": order.status,
                    "total": Decimal(order.total or 0),
                    "created_at": order.created_at,
                    "delivery_type": order.delivery_type,
                }
            )
        return out

    # ------------------------------------------------------------------ customers
    async def customer_kpis(self, *, empresa_id: UUID) -> dict[str, Any]:
        # LTV per customer subquery
        lname = func.lower(func.trim(Cliente.full_name))
        oname = func.lower(func.trim(Order.customer_name))
        ltv_subq = (
            select(
                Cliente.id.label("id"),
                func.count(Order.id).label("order_count"),
                func.coalesce(func.sum(Order.total), 0).label("lifetime_value"),
                func.max(Order.created_at).label("last_purchase_at"),
                Cliente.created_at.label("customer_created_at"),
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
            .group_by(Cliente.id, Cliente.created_at)
            .subquery()
        )

        oc = ltv_subq.c.order_count
        lv = ltv_subq.c.lifetime_value
        lpa = ltv_subq.c.last_purchase_at
        c_created = ltv_subq.c.customer_created_at
        now = self._now()
        cutoff = now - _INACTIVE_CUTOFF_TIMEDELTA

        vip_flag = case(
            ((oc >= _VIP_MIN_ORDERS) | (lv >= _VIP_MIN_LIFETIME_VALUE), 1),
            else_=0,
        ).label("is_vip")
        recurrent_flag = case((oc >= _RECURRENT_MIN_ORDERS, 1), else_=0).label(
            "is_recurrent"
        )
        inactive_flag = case(
            (
                (lpa.is_not(None) & (lpa < cutoff))
                | (lpa.is_(None) & (c_created < cutoff)),
                1,
            ),
            else_=0,
        ).label("is_inactive")
        new_flag = case((oc == 0, 1), else_=0).label("is_new")
        active_flag = case(
            ((oc > 0) & lpa.is_not(None) & (lpa >= cutoff), 1),
            else_=0,
        ).label("is_active")

        agg_row = (
            await self._session.execute(
                select(
                    func.count(ltv_subq.c.id).label("total"),
                    func.coalesce(func.sum(vip_flag), 0).label("vip"),
                    func.coalesce(func.sum(recurrent_flag), 0).label("recurrent"),
                    func.coalesce(func.sum(inactive_flag), 0).label("inactive"),
                    func.coalesce(func.sum(new_flag), 0).label("new"),
                    func.coalesce(func.sum(active_flag), 0).label("active"),
                    func.coalesce(func.sum(lv), 0).label("total_ltv"),
                    func.coalesce(func.sum(oc), 0).label("total_orders"),
                )
            )
        ).one()

        total = int(agg_row.total or 0)
        total_orders = int(agg_row.total_orders or 0)
        total_ltv = Decimal(agg_row.total_ltv or 0)
        avg_ltv = (total_ltv / Decimal(total)) if total else Decimal("0")
        avg_orders = (
            (Decimal(total_orders) / Decimal(total)) if total else Decimal("0")
        )

        return {
            "total": total,
            "vip": int(agg_row.vip or 0),
            "recurrent": int(agg_row.recurrent or 0),
            "inactive": int(agg_row.inactive or 0),
            "active": int(agg_row.active or 0),
            "new": int(agg_row.new or 0),
            "average_lifetime_value": avg_ltv.quantize(Decimal("0.01")),
            "average_orders_per_customer": avg_orders.quantize(Decimal("0.01")),
        }

    async def customers_for_export(
        self, *, empresa_id: UUID, limit: int = 5000
    ) -> list[dict[str, Any]]:
        lname = func.lower(func.trim(Cliente.full_name))
        oname = func.lower(func.trim(Order.customer_name))
        ltv_subq = (
            select(
                Cliente.id.label("id"),
                func.count(Order.id).label("order_count"),
                func.coalesce(func.sum(Order.total), 0).label("lifetime_value"),
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
            .group_by(Cliente.id)
            .subquery()
        )
        rows = await self._session.execute(
            select(
                Cliente.full_name,
                Cliente.email,
                Cliente.phone,
                ltv_subq.c.order_count,
                ltv_subq.c.lifetime_value,
                ltv_subq.c.last_purchase_at,
            )
            .outerjoin(ltv_subq, ltv_subq.c.id == Cliente.id)
            .where(
                Cliente.empresa_id == empresa_id,
                Cliente.deleted_at.is_(None),
            )
            .order_by(ltv_subq.c.lifetime_value.desc().nulls_last())
            .limit(limit)
        )
        out: list[dict[str, Any]] = []
        for name, email, phone, oc, lv, last_purchase in rows.all():
            oc_i = int(oc or 0)
            lv_d = Decimal(lv or 0)
            is_vip = oc_i >= _VIP_MIN_ORDERS or lv_d >= _VIP_MIN_LIFETIME_VALUE
            is_recurrent = oc_i >= _RECURRENT_MIN_ORDERS
            out.append(
                {
                    "full_name": name or "Sin nombre",
                    "email": email,
                    "phone": phone,
                    "order_count": oc_i,
                    "lifetime_value": lv_d,
                    "last_purchase_at": last_purchase,
                    "is_vip": is_vip,
                    "is_recurrent": is_recurrent,
                }
            )
        return out

    async def top_customers(
        self, *, empresa_id: UUID, limit: int = 10
    ) -> list[dict[str, Any]]:
        customers = await self.customers_for_export(
            empresa_id=empresa_id, limit=limit
        )
        return [
            {
                "full_name": c["full_name"],
                "order_count": c["order_count"],
                "lifetime_value": c["lifetime_value"],
                "is_vip": c["is_vip"],
            }
            for c in customers
        ]

    # ------------------------------------------------------------------ pipeline
    async def pipeline_kpis(self, *, empresa_id: UUID) -> dict[str, Any]:
        rows = await self._session.execute(
            select(
                SalesPipelineItem.stage,
                func.count(SalesPipelineItem.id).label("count"),
                func.coalesce(
                    func.sum(SalesPipelineItem.estimated_value), 0
                ).label("value"),
            )
            .where(SalesPipelineItem.empresa_id == empresa_id)
            .group_by(SalesPipelineItem.stage)
        )
        by_stage: dict[str, dict[str, Any]] = {}
        for stage, count, value in rows.all():
            by_stage[stage] = {"count": int(count or 0), "value": Decimal(value or 0)}

        open_deals = sum(by_stage.get(s, {"count": 0})["count"] for s in OPEN_STAGES)
        won_deals = by_stage.get(WON_STAGE, {"count": 0})["count"]
        lost_deals = by_stage.get(LOST_STAGE, {"count": 0})["count"]

        weighted_q = select(
            func.coalesce(
                func.sum(
                    SalesPipelineItem.estimated_value
                    * SalesPipelineItem.probability
                    / literal_column("100")
                ),
                0,
            )
        ).where(
            SalesPipelineItem.empresa_id == empresa_id,
            SalesPipelineItem.stage.in_(tuple(OPEN_STAGES)),
        )
        weighted = Decimal((await self._session.execute(weighted_q)).scalar_one() or 0)

        won_value = by_stage.get(WON_STAGE, {"value": Decimal("0")})["value"]
        lost_value = by_stage.get(LOST_STAGE, {"value": Decimal("0")})["value"]
        open_value = sum(
            by_stage.get(s, {"value": Decimal("0")})["value"] for s in OPEN_STAGES
        )
        closed_total = won_deals + lost_deals
        conversion_pct = (
            round((won_deals / closed_total) * 100, 2) if closed_total > 0 else 0.0
        )
        return {
            "open_deals": open_deals,
            "won_deals": won_deals,
            "lost_deals": lost_deals,
            "total_value": open_value,
            "weighted_value": weighted,
            "won_value": won_value,
            "lost_value": lost_value,
            "conversion_pct": conversion_pct,
        }

    async def pipeline_funnel(self, *, empresa_id: UUID) -> list[dict[str, Any]]:
        rows = await self._session.execute(
            select(
                SalesPipelineItem.stage,
                func.count(SalesPipelineItem.id).label("count"),
                func.coalesce(
                    func.sum(SalesPipelineItem.estimated_value), 0
                ).label("value"),
            )
            .where(SalesPipelineItem.empresa_id == empresa_id)
            .group_by(SalesPipelineItem.stage)
        )
        by_stage: dict[str, dict[str, Any]] = {}
        for stage, count, value in rows.all():
            by_stage[stage] = {"count": int(count or 0), "value": Decimal(value or 0)}
        return [
            {
                "stage": stage,
                "count": by_stage.get(stage, {"count": 0})["count"],
                "value": by_stage.get(stage, {"value": Decimal("0")})["value"],
            }
            for stage in (
                "new_lead",
                "contacted",
                "qualified",
                "proposal",
                "negotiation",
                "won",
                "lost",
            )
        ]

    async def pipeline_deals_for_export(
        self, *, empresa_id: UUID, limit: int = 5000
    ) -> list[dict[str, Any]]:
        rows = await self._session.execute(
            select(
                SalesPipelineItem,
                Cliente.full_name.label("customer_name"),
            )
            .outerjoin(
                Cliente, Cliente.id == SalesPipelineItem.customer_id
            )
            .where(SalesPipelineItem.empresa_id == empresa_id)
            .order_by(SalesPipelineItem.created_at.desc())
            .limit(limit)
        )
        out: list[dict[str, Any]] = []
        for deal, customer_name in rows.all():
            out.append(
                {
                    "title": deal.title or "Sin título",
                    "stage": deal.stage,
                    "value": Decimal(deal.estimated_value or 0),
                    "probability": int(deal.probability or 0),
                    "customer_name": customer_name or "Sin cliente",
                    "created_at": deal.created_at,
                    "expected_close_date": deal.stage_entered_at,
                }
            )
        return out

    # ------------------------------------------------------------------ inventory
    async def inventory_kpis(self, *, empresa_id: UUID) -> dict[str, Any]:
        value_expr = func.coalesce(
            func.sum(
                InventoryItem.stock_actual * func.coalesce(Producto.base_price, 0)
            ),
            0,
        )
        units_expr = func.coalesce(func.sum(InventoryItem.stock_actual), 0)
        reserved_expr = func.coalesce(func.sum(InventoryItem.stock_reservado), 0)
        out_expr = func.coalesce(
            func.sum(case((InventoryItem.stock_actual <= 0, 1), else_=0)), 0
        )
        low_expr = func.coalesce(
            func.sum(
                case(
                    (
                        (InventoryItem.stock_actual > 0)
                        & (InventoryItem.stock_actual <= InventoryItem.stock_minimo),
                        1,
                    ),
                    else_=0,
                )
            ),
            0,
        )
        normal_expr = func.coalesce(
            func.sum(
                case(
                    (
                        InventoryItem.stock_actual > InventoryItem.stock_minimo,
                        1,
                    ),
                    else_=0,
                )
            ),
            0,
        )
        total_products = int(
            (
                await self._session.execute(
                    select(func.count()).select_from(Producto).where(
                        Producto.empresa_id == empresa_id,
                        Producto.deleted_at.is_(None),
                    )
                )
            ).scalar_one()
        )
        result = await self._session.execute(
            select(value_expr, units_expr, reserved_expr, out_expr, low_expr, normal_expr)
            .select_from(Producto)
            .outerjoin(
                InventoryItem,
                (InventoryItem.product_id == Producto.id)
                & (InventoryItem.empresa_id == empresa_id),
            )
            .where(Producto.empresa_id == empresa_id, Producto.deleted_at.is_(None))
        )
        value, units, reserved, out_of_stock, low_stock, normal_stock = result.one()
        return {
            "total_products": total_products,
            "out_of_stock": int(out_of_stock),
            "low_stock": int(low_stock),
            "normal_stock": int(normal_stock),
            "inventory_value": Decimal(value or 0),
            "total_units": int(units or 0),
            "total_reserved_units": int(reserved or 0),
        }

    async def inventory_for_export(
        self, *, empresa_id: UUID, limit: int = 5000
    ) -> list[dict[str, Any]]:
        stmt = (
            select(
                Producto.id.label("product_id"),
                Producto.name.label("name"),
                Producto.category.label("category"),
                Producto.slug.label("sku"),
                func.coalesce(Producto.base_price, 0).label("base_price"),
                func.coalesce(InventoryItem.stock_actual, 0).label("stock_actual"),
                func.coalesce(InventoryItem.stock_minimo, 0).label("stock_minimo"),
                func.coalesce(InventoryItem.stock_reservado, 0).label(
                    "stock_reservado"
                ),
            )
            .select_from(Producto)
            .outerjoin(
                InventoryItem,
                (InventoryItem.product_id == Producto.id)
                & (InventoryItem.empresa_id == empresa_id),
            )
            .where(Producto.empresa_id == empresa_id, Producto.deleted_at.is_(None))
            .order_by(Producto.name.asc())
            .limit(limit)
        )
        rows = await self._session.execute(stmt)
        out: list[dict[str, Any]] = []
        for (
            product_id,
            name,
            category,
            sku,
            base_price,
            stock_actual,
            stock_minimo,
            stock_reservado,
        ) in rows.all():
            stock_a = int(stock_actual or 0)
            stock_m = int(stock_minimo or 0)
            if stock_a <= 0:
                status = "agotado"
            elif stock_a <= stock_m:
                status = "stock_bajo"
            else:
                status = "normal"
            out.append(
                {
                    "product_id": product_id,
                    "name": name or "Sin nombre",
                    "category": category or "Sin categoría",
                    "sku": sku or "",
                    "base_price": Decimal(base_price or 0),
                    "stock_actual": stock_a,
                    "stock_minimo": stock_m,
                    "stock_reservado": int(stock_reservado or 0),
                    "status": status,
                }
            )
        return out

    async def top_products(
        self, *, empresa_id: UUID, limit: int = 10
    ) -> list[dict[str, Any]]:
        stmt = (
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
                & (OrderItem.empresa_id == empresa_id),
            )
            .outerjoin(
                Order,
                (Order.id == OrderItem.order_id) & (Order.status != "cancelled"),
            )
            .where(
                Producto.empresa_id == empresa_id,
                Producto.deleted_at.is_(None),
            )
            .group_by(Producto.id, Producto.name)
            .order_by(func.coalesce(func.sum(OrderItem.quantity), 0).desc())
            .limit(limit)
        )
        rows = await self._session.execute(stmt)
        return [
            {
                "product_id": row.product_id,
                "name": row.name,
                "units_sold": int(row.units_sold or 0),
                "revenue": Decimal(row.revenue or 0),
            }
            for row in rows.all()
        ]

    async def lowest_stock(
        self, *, empresa_id: UUID, limit: int = 10
    ) -> list[dict[str, Any]]:
        stmt = (
            select(
                Producto.id.label("product_id"),
                Producto.name.label("name"),
                func.coalesce(InventoryItem.stock_actual, 0).label("stock_actual"),
                func.coalesce(InventoryItem.stock_minimo, 0).label("stock_minimo"),
            )
            .select_from(Producto)
            .outerjoin(
                InventoryItem,
                (InventoryItem.product_id == Producto.id)
                & (InventoryItem.empresa_id == empresa_id),
            )
            .where(Producto.empresa_id == empresa_id, Producto.deleted_at.is_(None))
            .order_by(func.coalesce(InventoryItem.stock_actual, 0).asc())
            .limit(limit)
        )
        rows = await self._session.execute(stmt)
        out: list[dict[str, Any]] = []
        for product_id, name, stock_actual, stock_minimo in rows.all():
            stock_a = int(stock_actual or 0)
            stock_m = int(stock_minimo or 0)
            status = (
                "agotado"
                if stock_a <= 0
                else "stock_bajo"
                if stock_a <= stock_m
                else "normal"
            )
            out.append(
                {
                    "product_id": product_id,
                    "name": name,
                    "stock_actual": stock_a,
                    "stock_minimo": stock_m,
                    "status": status,
                }
            )
        return out

    # ------------------------------------------------------------------ alerts
    async def inventory_critical_alerts(
        self, *, empresa_id: UUID, limit: int = 10
    ) -> list[str]:
        rows = await self.lowest_stock(empresa_id=empresa_id, limit=limit)
        return [
            f"{r['name']}: stock {r['stock_actual']} / mínimo {r['stock_minimo']} ({r['status']})"
            for r in rows
            if r["status"] != "normal"
        ]

    async def delayed_orders_alerts(
        self, *, empresa_id: UUID, limit: int = 10
    ) -> list[str]:
        now = self._now()
        threshold = now - timedelta(days=3)
        rows = await self._session.execute(
            select(
                Order.order_number,
                Order.customer_name,
                Order.status,
                Order.created_at,
            )
            .where(
                Order.empresa_id == empresa_id,
                Order.status.in_(_OPEN_ORDER_STATUSES),
                Order.created_at < threshold,
            )
            .order_by(Order.created_at.asc())
            .limit(limit)
        )
        out: list[str] = []
        for order_number, customer_name, status, created_at in rows.all():
            days = (now - created_at).days if created_at else 0
            out.append(
                f"{order_number or 'N/A'} - {customer_name or 'Sin nombre'} - {status} - {days}d"
            )
        return out

    # ------------------------------------------------------------------ forecast
    async def forecast(self, *, empresa_id: UUID) -> dict[str, Any]:
        monthly = await self.monthly_sales(empresa_id=empresa_id, months=12)
        revenue_values = [
            Decimal(m["revenue"]) for m in monthly if Decimal(m["revenue"]) > 0
        ]
        sample_size = len(revenue_values)
        if sample_size == 0:
            return {
                "monthly": Decimal("0"),
                "quarterly": Decimal("0"),
                "confidence": "low",
                "sample_size": 0,
            }
        avg_month = sum(revenue_values, Decimal("0")) / Decimal(sample_size)
        if sample_size >= 6:
            confidence = "high"
        elif sample_size >= 3:
            confidence = "medium"
        else:
            confidence = "low"
        return {
            "monthly": avg_month.quantize(Decimal("0.01")),
            "quarterly": (avg_month * Decimal("3")).quantize(Decimal("0.01")),
            "confidence": confidence,
            "sample_size": sample_size,
        }

    # ------------------------------------------------------------------ AI recs
    async def ai_recommendations(
        self, *, empresa_id: UUID, limit: int = 5
    ) -> list[dict[str, Any]]:
        recs: list[dict[str, Any]] = []
        # 1) hot leads
        hot = await self._session.execute(
            select(
                SalesPipelineItem.id,
                SalesPipelineItem.title,
                SalesPipelineItem.probability,
                SalesPipelineItem.estimated_value,
            )
            .where(
                SalesPipelineItem.empresa_id == empresa_id,
                SalesPipelineItem.stage.in_(("negotiation", "proposal")),
            )
            .order_by(SalesPipelineItem.probability.desc())
            .limit(limit)
        )
        for deal_id, title, prob, value in hot.all():
            recs.append(
                {
                    "id": f"hot_lead:{deal_id}",
                    "title": f"Lead caliente: {title or 'Sin título'}",
                    "description": (
                        f"Negociación abierta por S/ "
                        f"{Decimal(value or 0).quantize(Decimal('0.01'))} "
                        f"({int(prob or 0)}% de probabilidad)."
                    ),
                    "priority": "high" if int(prob or 0) >= 70 else "medium",
                }
            )
        # 2) low stock (operational risk)
        low = await self.lowest_stock(empresa_id=empresa_id, limit=3)
        for r in low:
            if r["status"] == "normal":
                continue
            recs.append(
                {
                    "id": f"low_stock:{r['product_id']}",
                    "title": f"Reposición urgente: {r['name']}",
                    "description": (
                        f"Stock actual {r['stock_actual']} - mínimo "
                        f"{r['stock_minimo']}."
                    ),
                    "priority": "high" if r["status"] == "agotado" else "medium",
                }
            )
        # 3) top product growth (last 30 days)
        from app.modules.orders.models import Order, OrderItem

        recent = await self._session.execute(
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
        for product_id, name, units in recent.all():
            recs.append(
                {
                    "id": f"producto_top:{product_id}",
                    "title": f"Producto con crecimiento: {name}",
                    "description": f"{int(units or 0)} unidades vendidas en los últimos 30 días.",
                    "priority": "medium",
                }
            )
        return recs[:limit]
