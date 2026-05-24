from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.conversations.models import Conversation, Message
from app.modules.conversations.schemas import (
    ConversationCreateRequest,
    ConversationUpdateRequest,
    MessageCreateRequest,
)


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_conversation(self, *, empresa_id: UUID, payload: ConversationCreateRequest) -> Conversation:
        conversation = Conversation(
            empresa_id=empresa_id,
            cliente_id=payload.cliente_id,
            asunto=payload.asunto,
            canal=payload.canal,
        )
        self._session.add(conversation)
        await self._session.flush()
        return conversation

    async def get_conversation_by_id(
        self, *, empresa_id: UUID, conversation_id: UUID
    ) -> Conversation | None:
        result = await self._session.execute(
            select(Conversation).where(
                Conversation.empresa_id == empresa_id,
                Conversation.id == conversation_id,
                Conversation.deleted_at.is_(None),
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
        estado: str | None = None,
    ) -> tuple[Sequence[Conversation], int]:
        query = self._filtered_query(empresa_id=empresa_id, search=search, estado=estado)
        count_result = await self._session.execute(select(func.count()).select_from(query.subquery()))
        total = int(count_result.scalar_one())

        result = await self._session.execute(
            query.order_by(Conversation.updated_at.desc()).limit(limit).offset(offset)
        )
        return result.scalars().all(), total

    async def update_conversation(
        self,
        *,
        conversation: Conversation,
        payload: ConversationUpdateRequest | dict,
    ) -> Conversation:
        values = payload.model_dump(exclude_unset=True) if not isinstance(payload, dict) else payload
        for field, value in values.items():
            setattr(conversation, field, value)
        await self._session.flush()
        return conversation

    async def soft_delete_conversation(self, *, conversation: Conversation) -> None:
        conversation.deleted_at = datetime.now(UTC)
        await self._session.flush()

    async def add_message(
        self,
        *,
        empresa_id: UUID,
        conversation_id: UUID,
        payload: MessageCreateRequest,
    ) -> Message:
        message = Message(
            empresa_id=empresa_id,
            conversation_id=conversation_id,
            role=payload.role,
            content=payload.content,
            sender_name=payload.sender_name,
            extra_data=payload.extra_data,
        )
        self._session.add(message)
        await self._session.flush()
        return message

    async def list_messages(
        self,
        *,
        empresa_id: UUID,
        conversation_id: UUID,
        limit: int,
        offset: int,
    ) -> tuple[Sequence[Message], int]:
        query = select(Message).where(
            Message.empresa_id == empresa_id,
            Message.conversation_id == conversation_id,
        )
        count_result = await self._session.execute(select(func.count()).select_from(query.subquery()))
        total = int(count_result.scalar_one())

        result = await self._session.execute(
            query.order_by(Message.created_at.asc()).limit(limit).offset(offset)
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
        estado: str | None,
    ) -> Select[tuple[Conversation]]:
        query = select(Conversation).where(
            Conversation.empresa_id == empresa_id,
            Conversation.deleted_at.is_(None),
        )
        if estado:
            query = query.where(Conversation.estado == estado)
        if search:
            pattern = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Conversation.asunto.ilike(pattern),
                )
            )
        return query
