from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.sales.api.service import SalesAPIService


async def get_sales_api_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SalesAPIService:
    return SalesAPIService(session=session)
