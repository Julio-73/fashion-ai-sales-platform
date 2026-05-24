from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.modules.chats.repository import ChatRepository
from app.modules.chats.service import ChatService


async def get_chat_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ChatRepository:
    return ChatRepository(session=session)


async def get_chat_service(
    repository: Annotated[ChatRepository, Depends(get_chat_repository)],
) -> ChatService:
    return ChatService(repository=repository)

