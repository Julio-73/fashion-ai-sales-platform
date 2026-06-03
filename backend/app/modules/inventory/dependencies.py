"""FastAPI dependencies for the Inventory Management module."""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.modules.inventory.repository import InventoryRepository
from app.modules.inventory.service import InventoryService


async def get_inventory_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> InventoryRepository:
    return InventoryRepository(session=session)


async def get_inventory_service(
    repository: Annotated[InventoryRepository, Depends(get_inventory_repository)],
) -> InventoryService:
    return InventoryService(repository=repository)
