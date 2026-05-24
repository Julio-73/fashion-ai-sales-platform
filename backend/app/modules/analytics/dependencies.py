from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.modules.analytics.repository import AnalyticsRepository
from app.modules.analytics.service import AnalyticsService


async def get_analytics_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AnalyticsRepository:
    return AnalyticsRepository(session=session)


async def get_analytics_service(
    repository: Annotated[AnalyticsRepository, Depends(get_analytics_repository)],
) -> AnalyticsService:
    return AnalyticsService(repository=repository)

