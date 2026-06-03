"""In-process domain event bus.

Provides a simple, decoupled pub/sub mechanism so the inventory module
can react to order lifecycle changes without modifying the OrderFlowEngine
or any other frozen module. Subscribers are coroutine callbacks; events
are dispatched sequentially within the publisher's task (best-effort,
fire-and-forget — failures are logged but do not roll back the
originating transaction).
"""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


logger = logging.getLogger("ai_sales_agent.events")


@dataclass(frozen=True)
class DomainEvent:
    """A lightweight, immutable domain event payload."""

    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=datetime.utcnow)


Subscriber = Callable[[DomainEvent], Awaitable[None]]


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[Subscriber]] = {}

    def subscribe(self, event_name: str, subscriber: Subscriber) -> None:
        self._subscribers.setdefault(event_name, []).append(subscriber)

    def unsubscribe(self, event_name: str, subscriber: Subscriber) -> None:
        if event_name in self._subscribers:
            try:
                self._subscribers[event_name].remove(subscriber)
            except ValueError:
                pass

    async def publish(self, event: DomainEvent) -> None:
        subs = list(self._subscribers.get(event.name, []))
        if not subs:
            return
        results = await asyncio.gather(
            *(self._safe_invoke(sub, event) for sub in subs),
            return_exceptions=False,
        )
        _ = results  # gather already collected exceptions per-task

    async def _safe_invoke(self, subscriber: Subscriber, event: DomainEvent) -> None:
        try:
            await subscriber(event)
        except Exception:  # noqa: BLE001
            logger.exception(
                "Event subscriber %s failed for event %s",
                getattr(subscriber, "__qualname__", subscriber),
                event.name,
            )


bus = EventBus()


# ---------------------------------------------------------------------------
# Event names
# ---------------------------------------------------------------------------

ORDER_CONFIRMED = "order.confirmed"
ORDER_CANCELLED = "order.cancelled"
