"""CRM Enterprise V1 — Customer 360 repository.

Computes Customer 360 analytics by joining the existing ``clientes`` and
``orders`` tables on a normalized ``customer_name`` match. The existing
``orders`` table stores ``customer_name`` as a free-form string, so the
JOIN is performed case-insensitively and with whitespace trimmed.

The repository is additive: it never writes to existing tables and never
modifies the existing customer / order repositories.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, case, func, literal, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.modules.customers.models import Cliente
from app.modules.orders.models import Order, OrderItem


# ─────────────────────────────────────────────────────────────────────
# Constants — VIP engine rules (mirrored in the service layer)
# ─────────────────────────────────────────────────────────────────────
VIP_MIN_ORDERS = 5
VIP_MIN_LIFETIME_VALUE = Decimal("1000")
RECURRENT_MIN_ORDERS = 3
INACTIVITY_THRESHOLD_DAYS = 90
INACTIVITY_THRESHOLD_TIMEDELTA = timedelta(days=INACTIVITY_THRESHOLD_DAYS)


@dataclass(frozen=True)
class CustomerOrderAggregates:
    customer_id: UUID
    order_count: int
    lifetime_value: Decimal
    first_purchase_at: datetime | None
    last_purchase_at: datetime | None


class CrmRepository:
    """Read-only repository that combines customers and orders data."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _customer_normalized(self):
        return case(
            (
                func.trim(Cliente.full_name) == "",
                literal("__no_name__"),
            ),
            else_=func.lower(func.trim(Cliente.full_name)),
        )

    def _order_aggregates_subquery(self) -> Select:
        """Group non-cancelled orders by a normalized ``customer_name`` value."""
        normalized = func.lower(func.trim(Order.customer_name)).label("normalized_name")
        total_expr = func.coalesce(
            func.sum(Order.total).filter(Order.status != "cancelled"),
            0,
        ).label("lifetime_value")
        return (
            select(
                normalized,
                func.count(Order.id).label("order_count"),
                total_expr,
                func.min(Order.created_at).label("first_purchase_at"),
                func.max(Order.created_at).label("last_purchase_at"),
            )
            .where(Order.customer_name.is_not(None))
            .group_by(normalized)
            .subquery()
        )

    def _customer_aggregates_subquery(self, *, empresa_id: UUID):
        """Join customers with the order-aggregates subquery, projecting
        only the columns the service needs. Using a flat subquery avoids
        the multi-element row issue that ``select(Cliente, ...)`` would
        introduce.
        """
        agg = self._order_aggregates_subquery()
        return (
            select(
                Cliente.id.label("id"),
                func.coalesce(agg.c.order_count, 0).label("order_count"),
                func.coalesce(agg.c.lifetime_value, 0).label("lifetime_value"),
                agg.c.first_purchase_at.label("first_purchase_at"),
                agg.c.last_purchase_at.label("last_purchase_at"),
            )
            .select_from(Cliente)
            .outerjoin(agg, agg.c.normalized_name == self._customer_normalized())
            .where(
                Cliente.deleted_at.is_(None),
                Cliente.empresa_id == empresa_id,
            )
            .subquery()
        )

    # ------------------------------------------------------------------
    # Public read API
    # ------------------------------------------------------------------

    async def list_customer_360(
        self,
        *,
        empresa_id: UUID,
        limit: int,
        offset: int,
        search: str | None = None,
        is_vip: bool | None = None,
        is_recurrent: bool | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
    ) -> tuple[Sequence, int]:
        # First, fetch the Cliente rows that match the filters. Sorting
        # and pagination are done here so we never pull more than we
        # need into memory.
        customer_query = select(Cliente).where(
            Cliente.empresa_id == empresa_id,
            Cliente.deleted_at.is_(None),
        )
        if search:
            pattern = f"%{search.strip()}%"
            customer_query = customer_query.where(
                or_(
                    Cliente.full_name.ilike(pattern),
                    Cliente.email.ilike(pattern),
                    Cliente.phone.ilike(pattern),
                    Cliente.whatsapp.ilike(pattern),
                    Cliente.instagram_username.ilike(pattern),
                )
            )
        if date_from:
            customer_query = customer_query.where(
                Cliente.created_at >= datetime.combine(date_from, time.min, tzinfo=UTC)
            )
        if date_to:
            customer_query = customer_query.where(
                Cliente.created_at <= datetime.combine(date_to, time.max, tzinfo=UTC)
            )

        # Build the aggregates subquery restricted to the customers that
        # already match the simple filters above, then join it back so
        # we can apply VIP / recurrent filters in SQL.
        agg_sub = self._customer_aggregates_subquery(empresa_id=empresa_id)
        if is_vip:
            agg_sub = agg_sub.where(
                or_(
                    agg_sub.c.order_count >= VIP_MIN_ORDERS,
                    agg_sub.c.lifetime_value >= VIP_MIN_LIFETIME_VALUE,
                )
            )
        if is_recurrent:
            agg_sub = agg_sub.where(agg_sub.c.order_count >= RECURRENT_MIN_ORDERS)

        # Combine the Cliente filter with the aggregates join so that
        # we can count and paginate the final set in one round-trip.
        agg_alias = agg_sub.alias("agg_filtered")
        combined = (
            select(Cliente, agg_alias.c.order_count, agg_alias.c.lifetime_value,
                   agg_alias.c.first_purchase_at, agg_alias.c.last_purchase_at)
            .join(agg_alias, agg_alias.c.id == Cliente.id)
        )

        # Sort.
        sort_columns = {
            "created_at": Cliente.created_at,
            "full_name": Cliente.full_name,
            "lifetime_value": agg_alias.c.lifetime_value,
            "last_purchase_at": agg_alias.c.last_purchase_at,
            "order_count": agg_alias.c.order_count,
        }
        sort_col = sort_columns.get(sort_by, Cliente.created_at)
        if sort_dir == "asc":
            combined = combined.order_by(sort_col.asc().nulls_last(), Cliente.id.asc())
        else:
            combined = combined.order_by(sort_col.desc().nulls_last(), Cliente.id.asc())

        count_query = select(func.count()).select_from(combined.subquery())
        total = int((await self._session.execute(count_query)).scalar_one())

        result = await self._session.execute(combined.limit(limit).offset(offset))
        return result.all(), total

    async def get_customer_360(self, *, empresa_id: UUID, customer_id: UUID):
        agg_sub = self._customer_aggregates_subquery(empresa_id=empresa_id).alias("a")
        query = (
            select(
                Cliente,
                agg_sub.c.order_count,
                agg_sub.c.lifetime_value,
                agg_sub.c.first_purchase_at,
                agg_sub.c.last_purchase_at,
            )
            .join(agg_sub, agg_sub.c.id == Cliente.id)
            .where(Cliente.id == customer_id)
            .limit(1)
        )
        result = await self._session.execute(query)
        return result.first()

    async def list_customer_orders(
        self,
        *,
        empresa_id: UUID,
        customer_id: UUID,
        limit: int,
        offset: int,
    ) -> tuple[Sequence, int]:
        # Resolve customer name once to match the orders table.
        customer_result = await self._session.execute(
            select(Cliente.full_name).where(
                Cliente.empresa_id == empresa_id,
                Cliente.id == customer_id,
                Cliente.deleted_at.is_(None),
            )
        )
        customer_name = customer_result.scalar_one_or_none()
        if customer_name is None:
            return [], 0

        normalized = func.lower(func.trim(customer_name))

        items_count_subquery = (
            select(
                OrderItem.order_id.label("oid"),
                func.count(OrderItem.id).label("items_count"),
            )
            .group_by(OrderItem.order_id)
            .subquery()
        )
        primary_product_subquery = (
            select(
                OrderItem.order_id.label("oid"),
                func.min(OrderItem.product_name).label("primary_product_name"),
            )
            .group_by(OrderItem.order_id)
            .subquery()
        )

        base = (
            select(
                Order,
                func.coalesce(items_count_subquery.c.items_count, 0).label("items_count"),
                func.coalesce(primary_product_subquery.c.primary_product_name, "").label(
                    "primary_product_name"
                ),
            )
            .outerjoin(items_count_subquery, items_count_subquery.c.oid == Order.id)
            .outerjoin(
                primary_product_subquery,
                primary_product_subquery.c.oid == Order.id,
            )
            .where(
                Order.empresa_id == empresa_id,
                func.lower(func.trim(Order.customer_name)) == normalized,
            )
            .order_by(Order.created_at.desc())
        )

        count_query = select(func.count()).select_from(base.subquery())
        total = int((await self._session.execute(count_query)).scalar_one())

        result = await self._session.execute(base.limit(limit).offset(offset))
        return result.all(), total

    async def aggregate_for_company(self, *, empresa_id: UUID) -> dict:
        """Return aggregate metrics for the entire tenant.

        The VIP / recurrent / inactive classification is computed in SQL
        using the same business rules as the service layer.
        """
        agg = self._order_aggregates_subquery()
        order_count = func.coalesce(agg.c.order_count, 0).label("order_count")
        lifetime_value = func.coalesce(agg.c.lifetime_value, 0).label("lifetime_value")
        last_purchase_at = agg.c.last_purchase_at.label("last_purchase_at")

        base = (
            select(
                Cliente.id.label("cid"),
                order_count,
                lifetime_value,
                last_purchase_at,
                Cliente.created_at.label("customer_created_at"),
            )
            .select_from(Cliente)
            .outerjoin(agg, agg.c.normalized_name == self._customer_normalized())
            .where(Cliente.empresa_id == empresa_id, Cliente.deleted_at.is_(None))
            .subquery()
        )

        now = datetime.now(UTC)
        inactivity_cutoff = now - INACTIVITY_THRESHOLD_TIMEDELTA

        # IMPORTANT: reference columns through the ``base`` subquery, not
        # the original expressions; reusing the original column variables
        # here causes SQLAlchemy to inject a second anonymous subquery
        # into the FROM clause, producing a cartesian product.
        oc = base.c.order_count
        lv = base.c.lifetime_value
        lpa = base.c.last_purchase_at
        c_created = base.c.customer_created_at

        vip_flag = case(
            (
                or_(
                    oc >= VIP_MIN_ORDERS,
                    lv >= VIP_MIN_LIFETIME_VALUE,
                ),
                1,
            ),
            else_=0,
        ).label("is_vip")

        recurrent_flag = case((oc >= RECURRENT_MIN_ORDERS, 1), else_=0).label("is_recurrent")

        inactive_flag = case(
            (
                or_(
                    and_(lpa.is_not(None), lpa < inactivity_cutoff),
                    and_(lpa.is_(None), c_created < inactivity_cutoff),
                ),
                1,
            ),
            else_=0,
        ).label("is_inactive")

        new_flag = case((oc == 0, 1), else_=0).label("is_new")

        active_flag = case(
            (
                and_(
                    oc > 0,
                    lpa.is_not(None),
                    lpa >= inactivity_cutoff,
                ),
                1,
            ),
            else_=0,
        ).label("is_active")

        aggregate_query = select(
            func.count(base.c.cid).label("total_customers"),
            func.coalesce(func.sum(lv), 0).label("total_lifetime_value"),
            func.coalesce(func.sum(oc), 0).label("total_orders"),
            func.coalesce(func.sum(vip_flag), 0).label("vip_count"),
            func.coalesce(func.sum(recurrent_flag), 0).label("recurrent_count"),
            func.coalesce(func.sum(inactive_flag), 0).label("inactive_count"),
            func.coalesce(func.sum(new_flag), 0).label("new_count"),
            func.coalesce(func.sum(active_flag), 0).label("active_count"),
        )

        result = (await self._session.execute(aggregate_query)).one()
        total_orders = int(result.total_orders or 0)
        total_customers = int(result.total_customers or 0)
        total_lifetime = Decimal(result.total_lifetime_value or 0)
        average_ticket = (
            Decimal(total_lifetime / total_orders) if total_orders else Decimal("0")
        )
        average_orders = (
            Decimal(total_orders) / Decimal(total_customers) if total_customers else Decimal("0")
        )

        return {
            "total_customers": total_customers,
            "total_lifetime_value": total_lifetime,
            "average_ticket": average_ticket,
            "average_orders_per_customer": average_orders,
            "vip_count": int(result.vip_count or 0),
            "recurrent_count": int(result.recurrent_count or 0),
            "inactive_count": int(result.inactive_count or 0),
            "new_count": int(result.new_count or 0),
            "active_count": int(result.active_count or 0),
        }
