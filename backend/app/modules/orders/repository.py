from collections.abc import Sequence
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.orders.models import Order, OrderItem
from app.modules.orders.schemas import OrderCreateRequest


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, empresa_id: UUID, order_number: str, payload: OrderCreateRequest) -> Order:
        total = sum(item.price * item.quantity for item in payload.items)
        order = Order(
            empresa_id=empresa_id,
            order_number=order_number,
            customer_name=payload.customer_name.strip(),
            customer_phone=payload.customer_phone,
            delivery_type=payload.delivery_type,
            delivery_address=payload.delivery_address,
            status=payload.status,
            total=total,
        )
        self._session.add(order)
        await self._session.flush()
        for item in payload.items:
            self._session.add(
                OrderItem(
                    empresa_id=empresa_id,
                    order_id=order.id,
                    **item.model_dump(),
                )
            )
        await self._session.flush()
        await self._session.refresh(order, attribute_names=["items"])
        return order

    async def get_by_id(self, *, empresa_id: UUID, order_id: UUID) -> Order | None:
        result = await self._session.execute(
            select(Order)
            .options(joinedload(Order.items))
            .where(Order.empresa_id == empresa_id, Order.id == order_id)
        )
        return result.unique().scalar_one_or_none()

    async def list(
        self,
        *,
        empresa_id: UUID,
        limit: int,
        offset: int,
        status: str | None = None,
        customer: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> tuple[Sequence[Order], int]:
        query = self._filtered_query(
            empresa_id=empresa_id,
            status=status,
            customer=customer,
            date_from=date_from,
            date_to=date_to,
        )
        total_result = await self._session.execute(select(func.count()).select_from(query.subquery()))
        total = int(total_result.scalar_one())
        result = await self._session.execute(
            query.options(joinedload(Order.items))
            .order_by(Order.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.unique().scalars().all(), total

    async def update_status(self, *, order: Order, status: str) -> Order:
        order.status = status
        await self._session.flush()
        await self._session.refresh(order, attribute_names=["items"])
        return order

    async def metrics(self, *, empresa_id: UUID) -> tuple[int, int, int, Decimal]:
        now = datetime.now(UTC)
        today_start = datetime.combine(now.date(), time.min, tzinfo=UTC)
        week_start = today_start - timedelta(days=today_start.weekday())
        month_start = today_start.replace(day=1)

        async def count_since(start: datetime) -> int:
            result = await self._session.execute(
                select(func.count()).select_from(Order).where(
                    Order.empresa_id == empresa_id,
                    Order.created_at >= start,
                )
            )
            return int(result.scalar_one())

        total_sales_result = await self._session.execute(
            select(func.coalesce(func.sum(Order.total), 0)).where(
                Order.empresa_id == empresa_id,
                Order.status != "cancelled",
            )
        )
        return (
            await count_since(today_start),
            await count_since(week_start),
            await count_since(month_start),
            Decimal(total_sales_result.scalar_one()),
        )

    async def next_count(self, *, empresa_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(Order).where(Order.empresa_id == empresa_id)
        )
        return int(result.scalar_one()) + 1

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    def _filtered_query(
        self,
        *,
        empresa_id: UUID,
        status: str | None,
        customer: str | None,
        date_from: date | None,
        date_to: date | None,
    ) -> Select[tuple[Order]]:
        query = select(Order).where(Order.empresa_id == empresa_id)
        if status:
            query = query.where(Order.status == status)
        if customer:
            pattern = f"%{customer.strip()}%"
            query = query.where(or_(Order.customer_name.ilike(pattern), Order.customer_phone.ilike(pattern)))
        if date_from:
            query = query.where(Order.created_at >= datetime.combine(date_from, time.min, tzinfo=UTC))
        if date_to:
            query = query.where(Order.created_at <= datetime.combine(date_to, time.max, tzinfo=UTC))
        return query
