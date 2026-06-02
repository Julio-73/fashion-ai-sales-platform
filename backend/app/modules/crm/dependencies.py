"""CRM Enterprise V1 — Customer 360 dependencies."""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.modules.crm.repository import CrmRepository
from app.modules.crm.service import CrmService


async def get_crm_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CrmRepository:
    return CrmRepository(session=session)


async def get_crm_service(
    repository: Annotated[CrmRepository, Depends(get_crm_repository)],
) -> CrmService:
    return CrmService(repository=repository)
