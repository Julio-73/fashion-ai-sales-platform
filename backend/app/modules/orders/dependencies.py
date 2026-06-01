from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.modules.orders.repository import OrderRepository
from app.modules.orders.service import OrderService


async def get_order_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> OrderRepository:
    return OrderRepository(session=session)


async def get_order_service(
    repository: Annotated[OrderRepository, Depends(get_order_repository)],
) -> OrderService:
    return OrderService(repository=repository)
