from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.companies.models import Empresa


class CompanyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, *, empresa_id: UUID) -> Empresa | None:
        result = await self._session.execute(select(Empresa).where(Empresa.id == empresa_id))
        return result.scalar_one_or_none()

