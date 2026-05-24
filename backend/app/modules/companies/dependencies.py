from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.modules.companies.repository import CompanyRepository
from app.modules.companies.service import CompanyService


async def get_company_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CompanyRepository:
    return CompanyRepository(session=session)


async def get_company_service(
    repository: Annotated[CompanyRepository, Depends(get_company_repository)],
) -> CompanyService:
    return CompanyService(repository=repository)

