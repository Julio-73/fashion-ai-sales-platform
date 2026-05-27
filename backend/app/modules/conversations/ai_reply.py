import logging
from uuid import UUID

from app.modules.conversations.dtos import MessageDTO
from app.modules.conversations.models import Message as MessageModel
from app.modules.conversations.repository import ConversationRepository
from app.modules.conversations.schemas import MessageResponse
from app.smart_sales.brain import SmartSalesBrain
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("ai_sales_agent.conversations.ai_reply")


class AutoReplyGenerator:
    def __init__(
        self,
        session: AsyncSession,
        repository: ConversationRepository,
    ) -> None:
        self._session = session
        self._repository = repository
        self._brain = SmartSalesBrain(session=session)

    async def generate_and_save(
        self,
        *,
        empresa_id: UUID,
        conversation_id: UUID,
    ) -> MessageResponse | None:
        conversation = await self._repository.get_conversation_by_id(
            empresa_id=empresa_id, conversation_id=conversation_id
        )
        if not conversation:
            return None

        messages, _ = await self._repository.list_messages(
            empresa_id=empresa_id, conversation_id=conversation_id, limit=50, offset=0
        )
        if not messages:
            return None

        last_messages = [m.content for m in messages[-5:]]
        last_user_msg = last_messages[-1] if last_messages else ""
        if not last_user_msg:
            return None

        response_text = await self._brain.generate_reply(
            empresa_id=empresa_id,
            user_message=last_user_msg,
            conversation_id=conversation_id,
        )
        if not response_text:
            return None

        db_msg = MessageModel(
            empresa_id=empresa_id,
            conversation_id=conversation_id,
            role="agent",
            content=response_text,
            sender_name="AI Asistente",
        )
        self._session.add(db_msg)
        await self._session.flush()
        await self._repository.commit()

        return MessageResponse.model_validate(MessageDTO.model_validate(db_msg))
