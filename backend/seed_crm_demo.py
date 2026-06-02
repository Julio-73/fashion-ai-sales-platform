"""Seed sample orders for the Customer 360 demo.

This script is additive: it does not modify ``seed.py`` or the existing
order/AI/conversation modules. It creates a small set of orders that
exercise the VIP engine and lifecycle status classification so the
CRM dashboard has meaningful data to display.
"""
from __future__ import annotations

import asyncio
import logging
import random
import sys
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select

from app.core.config import get_settings
from app.database.session import AsyncSessionLocal
from app.modules.companies.models import Empresa
from app.modules.customers.models import Cliente
# Import the products module to register its table in the metadata so
# the order_items.product_id FK can be resolved during delete cascades.
from app.modules.products import models as _products_models  # noqa: F401
from app.modules.orders.models import Order, OrderItem
from app.modules.orders.repository import OrderRepository
from app.modules.orders.schemas import (
    OrderCreateRequest,
    OrderItemCreateRequest,
)

logger = logging.getLogger("ai_sales_agent.seed_crm_demo")

CUSTOMER_PROFILES = [
    # (name match, target_orders, target_ltv_pen, days_since_last)
    ("Carolina", 7, 2500, 5),       # VIP
    ("Patricia", 4, 850, 15),       # RECURRENTE
    ("Ximena", 3, 600, 20),         # RECURRENTE
    ("Alejandro", 6, 1700, 10),     # VIP
    ("María", 2, 350, 7),           # ACTIVO
    ("Luciana", 1, 120, 3),         # ACTIVO
    ("Andrea", 8, 3200, 30),        # VIP
    ("Valentina", 1, 89, 1),        # ACTIVO
    ("Camila", 0, 0, None),         # NUEVO
    ("Diego", 0, 0, None),          # NUEVO
    ("Gabriela", 2, 280, 120),      # INACTIVO (>90d)
    ("Sergio", 0, 0, None),         # NUEVO
]

PRODUCT_NAMES = [
    "Vestido floral primavera",
    "Blusa seda premium",
    "Pantalón sastre",
    "Chaqueta denim",
    "Falda midi",
    "Top bordado",
    "Conjunto ejecutivo",
    "Abrigo invierno",
]

SIZES = ["XS", "S", "M", "L"]
COLORS = ["Negro", "Blanco", "Beige", "Azul", "Verde"]


async def _generate_orders_for_customer(
    session,
    customer: Cliente,
    *,
    target_orders: int,
    target_ltv: Decimal,
    days_since_last: int | None,
) -> None:
    """Generate ``target_orders`` orders for ``customer`` whose total
    value is approximately ``target_ltv``.
    """
    if target_orders == 0:
        return

    repo = OrderRepository(session)
    base_count = await repo.next_count(empresa_id=customer.empresa_id)
    order_number = lambda n: f"ORD-{base_count + n:06d}"

    # Generate orders spread out in time. The most recent order is
    # ``days_since_last`` days ago.
    base_ltv = Decimal(target_ltv) / Decimal(target_orders)
    random.seed(hash(customer.id) & 0xFFFFFFFF)
    for i in range(target_orders):
        n_items = random.randint(1, 3)
        items: list[OrderItemCreateRequest] = []
        order_total = Decimal("0")
        for _ in range(n_items):
            price = Decimal(random.randint(80, 320))
            qty = random.randint(1, 2)
            items.append(
                OrderItemCreateRequest(
                    product_name=random.choice(PRODUCT_NAMES),
                    size=random.choice(SIZES),
                    color=random.choice(COLORS),
                    quantity=qty,
                    price=price,
                )
            )
            order_total += price * qty
        # Scale the order total so the sum hits the target.
        scale = base_ltv / max(order_total, Decimal("1"))
        items = [
            OrderItemCreateRequest(
                product_name=it.product_name,
                size=it.size,
                color=it.color,
                quantity=it.quantity,
                price=(it.price * scale).quantize(Decimal("0.01")),
            )
            for it in items
        ]
        scaled_total = sum(it.price * it.quantity for it in items)
        # Spread order creation: oldest is further in the past.
        days_ago = (days_since_last or 0) + (target_orders - i - 1) * 14
        from datetime import datetime, timedelta, timezone

        created_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
        order = Order(
            empresa_id=customer.empresa_id,
            order_number=order_number(i),
            customer_name=customer.full_name,
            customer_phone=customer.phone or customer.whatsapp,
            delivery_type="delivery",
            delivery_address=None,
            status="delivered" if days_ago > 0 else "confirmed",
            total=scaled_total,
        )
        session.add(order)
        await session.flush()
        order.created_at = created_at
        order.updated_at = created_at
        for it in items:
            session.add(
                OrderItem(
                    empresa_id=customer.empresa_id,
                    order_id=order.id,
                    product_name=it.product_name,
                    size=it.size,
                    color=it.color,
                    quantity=it.quantity,
                    price=it.price,
                    created_at=created_at,
                    updated_at=created_at,
                )
            )
        await session.flush()


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    async with AsyncSessionLocal() as session:
        emp = (await session.execute(select(Empresa).limit(1))).scalar_one_or_none()
        if emp is None:
            logger.error("No empresa found, run seed.py first")
            sys.exit(1)

        # Clean previous demo orders for this tenant so the script is
        # idempotent. Use raw SQL to avoid the ORM needing the full
        # mapper graph for cascade resolution.
        from sqlalchemy import text

        await session.execute(
            text("DELETE FROM order_items WHERE empresa_id = :empresa_id"),
            {"empresa_id": str(emp.id)},
        )
        deleted = await session.execute(
            text("DELETE FROM orders WHERE empresa_id = :empresa_id"),
            {"empresa_id": str(emp.id)},
        )
        await session.flush()
        logger.info("Removed existing orders for tenant: %s", deleted.rowcount)

        customers = (
            await session.execute(
                select(Cliente).where(Cliente.empresa_id == emp.id)
            )
        ).scalars().all()
        by_name_prefix = {c.full_name.split()[0]: c for c in customers}

        matched = 0
        for prefix, target_orders, target_ltv, days_since_last in CUSTOMER_PROFILES:
            customer = by_name_prefix.get(prefix)
            if customer is None:
                logger.warning("Customer prefix not found: %s", prefix)
                continue
            await _generate_orders_for_customer(
                session,
                customer,
                target_orders=target_orders,
                target_ltv=Decimal(target_ltv),
                days_since_last=days_since_last,
            )
            matched += 1

        await session.commit()
        logger.info("Generated orders for %s customers", matched)


if __name__ == "__main__":
    asyncio.run(main())
