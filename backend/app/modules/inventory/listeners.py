"""Decoupled listener that reacts to order events and updates stock.

Wired into the in-process event bus from ``app.main`` at startup.
Each event gets its own DB session so failures are isolated from the
order write path.
"""
from __future__ import annotations

import logging

from app.core.events import (
    ORDER_CANCELLED,
    ORDER_CONFIRMED,
    DomainEvent,
    bus,
)
from app.database.session import AsyncSessionLocal
from app.modules.inventory.repository import InventoryRepository
from app.modules.inventory.service import InventoryService


logger = logging.getLogger("ai_sales_agent.inventory.listener")


async def _on_order_event(event: DomainEvent) -> None:
    payload = event.payload
    empresa_id = payload.get("empresa_id")
    order_id = payload.get("order_id")
    order_number = payload.get("order_number")
    status = payload.get("current_status")
    items = payload.get("items") or []
    if not (empresa_id and order_id and status and items):
        return
    try:
        from uuid import UUID

        async with AsyncSessionLocal() as session:
            inventory_repo = InventoryRepository(session=session)
            inventory_service = InventoryService(repository=inventory_repo)
            await inventory_service.handle_order_event(
                empresa_id=UUID(empresa_id),
                order_id=UUID(order_id),
                order_number=order_number or "",
                status=status,
                items=items,
            )
    except Exception:  # noqa: BLE001
        logger.exception(
            "Inventory listener failed for order %s event %s", order_id, event.name
        )


def register_inventory_listener() -> None:
    """Idempotent: registers subscribers for order events."""
    bus.subscribe(ORDER_CONFIRMED, _on_order_event)
    bus.subscribe(ORDER_CANCELLED, _on_order_event)
    logger.info("Inventory listener registered for %s / %s", ORDER_CONFIRMED, ORDER_CANCELLED)


def unregister_inventory_listener() -> None:
    bus.unsubscribe(ORDER_CONFIRMED, _on_order_event)
    bus.unsubscribe(ORDER_CANCELLED, _on_order_event)
