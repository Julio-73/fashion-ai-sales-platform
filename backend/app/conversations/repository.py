from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.conversations.models import ConversationCore, MessageCore
from app.conversations.schemas import ConversationCoreCreateRequest, MessageCoreCreateRequest


class ConversationCoreRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_conversation(
        self, *, empresa_id: UUID, payload: ConversationCoreCreateRequest
    ) -> ConversationCore:
        conversation = ConversationCore(
            empresa_id=empresa_id,
            customer_id=payload.customer_id,
            status=payload.status,
        )
        self._session.add(conversation)
        await self._session.flush()
        return conversation

    async def get_conversation_by_id(
        self, *, empresa_id: UUID, conversation_id: UUID
    ) -> ConversationCore | None:
        result = await self._session.execute(
            select(ConversationCore).where(
                ConversationCore.empresa_id == empresa_id,
                ConversationCore.id == conversation_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_conversations(
        self,
        *,
        empresa_id: UUID,
        limit: int,
        offset: int,
        search: str | None = None,
        status: str | None = None,
    ) -> tuple[Sequence[ConversationCore], int]:
        query = self._filtered_query(empresa_id=empresa_id, search=search, status=status)
        count_result = await self._session.execute(select(func.count()).select_from(query.subquery()))
        total = int(count_result.scalar_one())

        result = await self._session.execute(
            query.order_by(ConversationCore.updated_at.desc()).limit(limit).offset(offset)
        )
        return result.scalars().all(), total

    async def update_conversation(
        self,
        *,
        conversation: ConversationCore,
        status: str | None,
    ) -> ConversationCore:
        if status is not None:
            conversation.status = status
        await self._session.flush()
        return conversation

    async def delete_conversation(self, *, conversation: ConversationCore) -> None:
        await self._session.delete(conversation)
        await self._session.flush()

    async def add_message(
        self,
        *,
        empresa_id: UUID,
        conversation_id: UUID,
        payload: MessageCoreCreateRequest,
    ) -> MessageCore:
        message = MessageCore(
            empresa_id=empresa_id,
            conversation_id=conversation_id,
            sender=payload.sender,
            content=payload.content,
        )
        self._session.add(message)
        await self._session.flush()
        return message

    async def update_last_message(
        self,
        *,
        conversation: ConversationCore,
        content: str,
    ) -> None:
        conversation.last_message = content[:200]
        await self._session.flush()

    async def list_messages(
        self,
        *,
        empresa_id: UUID,
        conversation_id: UUID,
        limit: int,
        offset: int,
    ) -> tuple[Sequence[MessageCore], int]:
        query = select(MessageCore).where(
            MessageCore.empresa_id == empresa_id,
            MessageCore.conversation_id == conversation_id,
        )
        count_result = await self._session.execute(select(func.count()).select_from(query.subquery()))
        total = int(count_result.scalar_one())

        result = await self._session.execute(
            query.order_by(MessageCore.created_at.asc()).limit(limit).offset(offset)
        )
        return result.scalars().all(), total

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    def _filtered_query(
        self,
        *,
        empresa_id: UUID,
        search: str | None,
        status: str | None,
    ) -> Select[tuple[ConversationCore]]:
        query = select(ConversationCore).where(
            ConversationCore.empresa_id == empresa_id,
        )
        if status:
            query = query.where(ConversationCore.status == status)
        if search:
            pattern = f"%{search.strip()}%"
            query = query.where(
                or_(
                    ConversationCore.last_message.ilike(pattern),
                )
            )
        return query
