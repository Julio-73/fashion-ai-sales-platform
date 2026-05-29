from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.modules.conversations.ai_reply import AutoReplyGenerator, TypingStateManager
from app.modules.conversations.repository import ConversationRepository
from app.modules.conversations.service import ConversationService


_typing_manager = TypingStateManager()


async def get_typing_manager() -> TypingStateManager:
    return _typing_manager


async def get_conversation_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ConversationRepository:
    return ConversationRepository(session=session)


async def get_conversation_service(
    repository: Annotated[ConversationRepository, Depends(get_conversation_repository)],
) -> ConversationService:
    return ConversationService(repository=repository)


async def get_auto_reply_generator(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    repository: Annotated[ConversationRepository, Depends(get_conversation_repository)],
    typing_manager: Annotated[TypingStateManager, Depends(get_typing_manager)],
) -> AutoReplyGenerator:
    return AutoReplyGenerator(session=session, repository=repository, typing_manager=typing_manager)
