from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.conversations.repository import ConversationCoreRepository
from app.conversations.service import ConversationCoreService
from app.database.session import get_db_session
from app.modules.customers.repository import CustomerRepository
from app.services.crm_bridge import CrmBridgeService


async def get_conversation_core_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ConversationCoreRepository:
    return ConversationCoreRepository(session=session)


async def get_customer_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CustomerRepository:
    return CustomerRepository(session=session)


async def get_crm_bridge_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    customer_repository: Annotated[CustomerRepository, Depends(get_customer_repository)],
) -> CrmBridgeService:
    return CrmBridgeService(
        session=session,
        customer_repository=customer_repository,
    )


async def get_conversation_core_service(
    repository: Annotated[ConversationCoreRepository, Depends(get_conversation_core_repository)],
    crm_bridge: Annotated[CrmBridgeService, Depends(get_crm_bridge_service)],
) -> ConversationCoreService:
    return ConversationCoreService(repository=repository, crm_bridge=crm_bridge)
