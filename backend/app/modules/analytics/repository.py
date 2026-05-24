from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.models import AnalyticsEvent


class AnalyticsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_recent_events(
        self,
        *,
        empresa_id: UUID,
        limit: int = 25,
    ) -> list[AnalyticsEvent]:
        result = await self._session.execute(
            select(AnalyticsEvent)
            .where(AnalyticsEvent.empresa_id == empresa_id)
            .order_by(AnalyticsEvent.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

