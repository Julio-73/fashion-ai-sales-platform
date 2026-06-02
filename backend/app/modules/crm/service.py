"""CRM Enterprise V1 — Customer 360 service.

Implements the VIP engine and lifecycle status classification, and
translates raw repository rows into Customer 360 DTOs.

The service is additive: it does not modify the existing customer or
order services.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from app.core.errors import AppError
from app.core.security.dependencies import TenantContext
from app.modules.crm.repository import (
    CrmRepository,
    INACTIVITY_THRESHOLD_DAYS,
    RECURRENT_MIN_ORDERS,
    VIP_MIN_LIFETIME_VALUE,
    VIP_MIN_ORDERS,
)
from app.modules.crm.schemas import (
    Customer360ListResponse,
    Customer360Summary,
    CustomerAggregateMetrics,
    CustomerLifecycleStatus,
    CustomerMetrics,
    CustomerOrderHistoryItem,
    CustomerOrderHistoryResponse,
)
from app.modules.customers.models import Cliente

logger = logging.getLogger("ai_sales_agent.crm")


def classify_lifecycle_status(
    *,
    order_count: int,
    lifetime_value: Decimal,
    days_since_last_purchase: int | None,
    customer_age_days: int,
) -> CustomerLifecycleStatus:
    """Apply the VIP engine rules.

    Order of evaluation (most specific wins):
    1. VIP — order_count >= 5 OR lifetime_value >= 1000
    2. RECURRENTE — order_count >= 3
    3. INACTIVO — last_purchase older than 90 days OR (no purchase
       AND customer older than 90 days)
    4. NUEVO — order_count == 0 and customer younger than 90 days
    5. ACTIVO — default fallback (has recent purchase)
    """
    if order_count >= VIP_MIN_ORDERS or lifetime_value >= VIP_MIN_LIFETIME_VALUE:
        return CustomerLifecycleStatus.VIP
    if order_count >= RECURRENT_MIN_ORDERS:
        return CustomerLifecycleStatus.RECURRENTE
    if order_count == 0:
        if customer_age_days > INACTIVITY_THRESHOLD_DAYS:
            return CustomerLifecycleStatus.INACTIVO
        return CustomerLifecycleStatus.NUEVO
    if days_since_last_purchase is not None and days_since_last_purchase > INACTIVITY_THRESHOLD_DAYS:
        return CustomerLifecycleStatus.INACTIVO
    return CustomerLifecycleStatus.ACTIVO


def _build_metrics_row(
    order_count: int,
    lifetime_value: Decimal,
    first_purchase_at: datetime | None,
    last_purchase_at: datetime | None,
) -> CustomerMetrics:
    days_since: int | None = None
    if last_purchase_at is not None:
        now = datetime.now(UTC)
        last = last_purchase_at if last_purchase_at.tzinfo else last_purchase_at.replace(tzinfo=UTC)
        days_since = max(0, (now - last).days)
    average_ticket = (
        Decimal(lifetime_value) / Decimal(order_count) if order_count else Decimal("0")
    )
    return CustomerMetrics(
        order_count=order_count,
        lifetime_value=Decimal(lifetime_value),
        average_ticket=average_ticket,
        first_purchase_at=first_purchase_at,
        last_purchase_at=last_purchase_at,
        days_since_last_purchase=days_since,
        status=CustomerLifecycleStatus.NUEVO,  # will be overwritten by service
    )


def _build_summary(
    cliente: Cliente,
    order_count: int,
    lifetime_value: Decimal,
    first_purchase_at: datetime | None,
    last_purchase_at: datetime | None,
) -> Customer360Summary:
    metrics = _build_metrics_row(
        order_count, lifetime_value, first_purchase_at, last_purchase_at
    )
    now = datetime.now(UTC)
    created = cliente.created_at if cliente.created_at.tzinfo else cliente.created_at.replace(tzinfo=UTC)
    customer_age_days = max(0, (now - created).days)

    days_since = metrics.days_since_last_purchase
    metrics.status = classify_lifecycle_status(
        order_count=order_count,
        lifetime_value=Decimal(lifetime_value),
        days_since_last_purchase=days_since,
        customer_age_days=customer_age_days,
    )

    return Customer360Summary(
        id=cliente.id,
        empresa_id=cliente.empresa_id,
        full_name=cliente.full_name,
        email=cliente.email,
        phone=cliente.phone,
        whatsapp=cliente.whatsapp,
        instagram_username=cliente.instagram_username,
        tags=list(cliente.tags or []),
        notes=cliente.notes,
        lead_status=cliente.lead_status,
        source=cliente.source,
        assigned_to=cliente.assigned_to,
        created_at=cliente.created_at,
        updated_at=cliente.updated_at,
        metrics=metrics,
    )


class CrmService:
    def __init__(self, repository: CrmRepository) -> None:
        self._repository = repository

    async def list_customer_360(
        self,
        *,
        tenant: TenantContext,
        limit: int,
        offset: int,
        search: str | None,
        is_vip: bool | None,
        is_recurrent: bool | None,
        date_from,
        date_to,
        sort_by: str,
        sort_dir: str,
        status_filter: str | None = None,
    ) -> Customer360ListResponse:
        # When filtering by lifecycle status we need to materialize the
        # full filtered set first because the lifecycle classifier runs
        # in Python. We cap the underlying fetch at 1000 records — a
        # reasonable bound for a CRM list view.
        fetch_limit = 1000 if status_filter and status_filter != "all" else limit
        fetch_offset = 0 if status_filter and status_filter != "all" else offset

        rows, total = await self._repository.list_customer_360(
            empresa_id=tenant.empresa_id,
            limit=fetch_limit,
            offset=fetch_offset,
            search=search,
            is_vip=is_vip,
            is_recurrent=is_recurrent,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )

        all_summaries: list[Customer360Summary] = []
        for row in rows:
            cliente, order_count, lifetime_value, first_purchase_at, last_purchase_at = row
            summary = _build_summary(
                cliente,
                int(order_count or 0),
                Decimal(lifetime_value or 0),
                first_purchase_at,
                last_purchase_at,
            )
            all_summaries.append(summary)

        if status_filter and status_filter != "all":
            filtered = [s for s in all_summaries if s.metrics.status.value == status_filter]
            total = len(filtered)
            items = filtered[offset : offset + limit]
        else:
            total = total
            items = all_summaries

        aggregate = await self._build_aggregate(items)
        logger.info(
            "crm.list_customer_360 empresa=%s total=%s returned=%s status=%s",
            tenant.empresa_id,
            total,
            len(items),
            status_filter,
        )
        return Customer360ListResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            aggregate=aggregate,
        )

    async def get_customer_360(
        self,
        *,
        tenant: TenantContext,
        customer_id: UUID,
    ) -> Customer360Summary:
        row = await self._repository.get_customer_360(
            empresa_id=tenant.empresa_id,
            customer_id=customer_id,
        )
        if row is None:
            raise AppError(code="customer_not_found", message="Customer not found", status_code=404)
        cliente, order_count, lifetime_value, first_purchase_at, last_purchase_at = row
        return _build_summary(
            cliente,
            int(order_count or 0),
            Decimal(lifetime_value or 0),
            first_purchase_at,
            last_purchase_at,
        )

    async def list_customer_orders(
        self,
        *,
        tenant: TenantContext,
        customer_id: UUID,
        limit: int,
        offset: int,
    ) -> CustomerOrderHistoryResponse:
        rows, total = await self._repository.list_customer_orders(
            empresa_id=tenant.empresa_id,
            customer_id=customer_id,
            limit=limit,
            offset=offset,
        )
        items: list[CustomerOrderHistoryItem] = []
        for row in rows:
            order, items_count, primary_product_name = row
            items.append(
                CustomerOrderHistoryItem(
                    order_id=order.id,
                    order_number=order.order_number,
                    created_at=order.created_at,
                    status=order.status,
                    total=Decimal(order.total),
                    items_count=int(items_count or 0),
                    primary_product_name=str(primary_product_name or ""),
                )
            )
        return CustomerOrderHistoryResponse(
            customer_id=customer_id,
            total=total,
            limit=limit,
            offset=offset,
            items=items,
        )

    async def get_metrics(self, *, tenant: TenantContext) -> CustomerAggregateMetrics:
        aggregate = await self._repository.aggregate_for_company(empresa_id=tenant.empresa_id)
        return CustomerAggregateMetrics(
            total_customers=int(aggregate["total_customers"]),
            new_customers=int(aggregate["new_count"]),
            active_customers=int(aggregate["active_count"]),
            recurrent_customers=int(aggregate["recurrent_count"]),
            vip_customers=int(aggregate["vip_count"]),
            inactive_customers=int(aggregate["inactive_count"]),
            total_lifetime_value=Decimal(aggregate["total_lifetime_value"]),
            average_ticket=Decimal(aggregate["average_ticket"]),
            average_orders_per_customer=Decimal(aggregate["average_orders_per_customer"]),
        )

    async def _build_aggregate(self, items: list[Customer360Summary]) -> CustomerAggregateMetrics:
        total = len(items)
        if total == 0:
            return CustomerAggregateMetrics()
        new = active = recurrent = vip = inactive = 0
        total_ltv = Decimal("0")
        total_orders = 0
        for item in items:
            total_ltv += item.metrics.lifetime_value
            total_orders += item.metrics.order_count
            match item.metrics.status:
                case CustomerLifecycleStatus.NUEVO:
                    new += 1
                case CustomerLifecycleStatus.ACTIVO:
                    active += 1
                case CustomerLifecycleStatus.RECURRENTE:
                    recurrent += 1
                case CustomerLifecycleStatus.VIP:
                    vip += 1
                case CustomerLifecycleStatus.INACTIVO:
                    inactive += 1
        average_ticket = (
            Decimal(total_ltv) / Decimal(total_orders) if total_orders else Decimal("0")
        )
        return CustomerAggregateMetrics(
            total_customers=total,
            new_customers=new,
            active_customers=active,
            recurrent_customers=recurrent,
            vip_customers=vip,
            inactive_customers=inactive,
            total_lifetime_value=total_ltv,
            average_ticket=average_ticket,
            average_orders_per_customer=Decimal(total_orders) / Decimal(total),
        )
