from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.chats.models import Chat


class ChatRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, *, empresa_id: UUID, chat_id: UUID) -> Chat | None:
        result = await self._session.execute(
            select(Chat).where(Chat.empresa_id == empresa_id, Chat.id == chat_id)
        )
        return result.scalar_one_or_none()

