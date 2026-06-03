from uuid import UUID

from app.core.errors import AppError
from app.core.events import DomainEvent, ORDER_CANCELLED, ORDER_CONFIRMED, bus
from app.core.security.dependencies import TenantContext
from app.modules.orders.repository import OrderRepository
from app.modules.orders.schemas import (
    OrderCreateRequest,
    OrderListResponse,
    OrderMetricsResponse,
    OrderResponse,
)


class OrderService:
    def __init__(self, repository: OrderRepository) -> None:
        self._repository = repository

    async def create_order(self, *, tenant: TenantContext, payload: OrderCreateRequest) -> OrderResponse:
        order_number = await self._build_order_number(tenant.empresa_id)
        order = await self._repository.create(
            empresa_id=tenant.empresa_id,
            order_number=order_number,
            payload=payload,
        )
        await self._repository.commit()
        await self._emit_status_event(order=order)
        return OrderResponse.model_validate(order)

    async def create_order_for_ai(self, *, empresa_id: UUID, payload: OrderCreateRequest) -> OrderResponse:
        order_number = await self._build_order_number(empresa_id)
        order = await self._repository.create(
            empresa_id=empresa_id,
            order_number=order_number,
            payload=payload,
        )
        await self._emit_status_event(order=order)
        return OrderResponse.model_validate(order)

    async def list_orders(
        self,
        *,
        tenant: TenantContext,
        limit: int,
        offset: int,
        status: str | None,
        customer: str | None,
        date_from,
        date_to,
    ) -> OrderListResponse:
        orders, total = await self._repository.list(
            empresa_id=tenant.empresa_id,
            limit=limit,
            offset=offset,
            status=status,
            customer=customer,
            date_from=date_from,
            date_to=date_to,
        )
        return OrderListResponse(
            items=[OrderResponse.model_validate(order) for order in orders],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def update_status(self, *, tenant: TenantContext, order_id: UUID, status: str) -> OrderResponse:
        order = await self._repository.get_by_id(empresa_id=tenant.empresa_id, order_id=order_id)
        if order is None:
            raise AppError(code="order_not_found", message="Order not found", status_code=404)
        previous_status = order.status
        updated = await self._repository.update_status(order=order, status=status)
        await self._repository.commit()
        # Only emit when the status actually changed, and only for the
        # transitions that downstream modules care about.
        if previous_status != status and status in {"confirmed", "cancelled"}:
            await self._emit_status_event(order=updated)
        return OrderResponse.model_validate(updated)

    async def get_metrics(self, *, tenant: TenantContext) -> OrderMetricsResponse:
        today, week, month, total_sales = await self._repository.metrics(empresa_id=tenant.empresa_id)
        return OrderMetricsResponse(
            orders_today=today,
            orders_week=week,
            orders_month=month,
            total_sales=total_sales,
        )

    async def _build_order_number(self, empresa_id: UUID) -> str:
        next_count = await self._repository.next_count(empresa_id=empresa_id)
        return f"ORD-{next_count:06d}"

    async def _emit_status_event(self, *, order) -> None:
        try:
            event_name = ORDER_CONFIRMED if order.status == "confirmed" else (
                ORDER_CANCELLED if order.status == "cancelled" else None
            )
            if event_name is None:
                return
            items_payload = [
                {
                    "product_id": str(item.product_id) if item.product_id else None,
                    "product_name": item.product_name,
                    "quantity": int(item.quantity),
                    "size": item.size,
                    "color": item.color,
                }
                for item in (order.items or [])
            ]
            await bus.publish(
                DomainEvent(
                    name=event_name,
                    payload={
                        "empresa_id": str(order.empresa_id),
                        "order_id": str(order.id),
                        "order_number": order.order_number,
                        "previous_status": None,
                        "current_status": order.status,
                        "items": items_payload,
                    },
                )
            )
        except Exception:  # noqa: BLE001
            # Event publishing must never break the order write path.
            import logging

            logging.getLogger("ai_sales_agent.orders").exception(
                "Failed to publish status event for order %s", order.id
            )
