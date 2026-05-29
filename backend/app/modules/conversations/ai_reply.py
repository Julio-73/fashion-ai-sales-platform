from datetime import UTC, datetime
import logging
from uuid import UUID

from app.modules.conversations.dtos import MessageDTO
from app.modules.conversations.models import Message as MessageModel
from app.modules.conversations.repository import ConversationRepository
from app.modules.conversations.schemas import (
    MessageCreateRequest,
    MessageResponse,
    ProcessMessageRequest,
    ProcessMessageResponse,
    TypingState,
)
from app.smart_sales.brain import SmartSalesBrain
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("ai_sales_agent.conversations.ai_reply")


class TypingStateManager:
    def __init__(self) -> None:
        self._typing: dict[str, bool] = {}

    def start_typing(self, conversation_id: str) -> None:
        self._typing[conversation_id] = True

    def stop_typing(self, conversation_id: str) -> None:
        self._typing[conversation_id] = False

    def is_typing(self, conversation_id: str) -> bool:
        return self._typing.get(conversation_id, False)

    def get_state(self, conversation_id: str) -> TypingState:
        return TypingState(is_typing=self.is_typing(conversation_id))


class AutoReplyGenerator:
    def __init__(
        self,
        session: AsyncSession,
        repository: ConversationRepository,
        typing_manager: TypingStateManager | None = None,
    ) -> None:
        self._session = session
        self._repository = repository
        self._brain = SmartSalesBrain(session=session)
        self._typing = typing_manager or TypingStateManager()

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

        self._typing.start_typing(str(conversation_id))
        try:
            response_text = await self._brain.generate_reply(
                empresa_id=empresa_id,
                user_message=last_user_msg,
                conversation_id=conversation_id,
            )
        finally:
            self._typing.stop_typing(str(conversation_id))

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

    async def process_message(
        self,
        *,
        empresa_id: UUID,
        conversation_id: UUID,
        payload: ProcessMessageRequest,
    ) -> ProcessMessageResponse:
        conversation = await self._repository.get_conversation_by_id(
            empresa_id=empresa_id, conversation_id=conversation_id
        )
        if not conversation:
            from app.core.errors import AppError
            raise AppError(code="conversation_not_found", message="Conversation not found", status_code=404)

        sender_name = payload.sender_name or (
            "Cliente" if payload.role == "client" else "Tú"
        )

        msg_payload = MessageCreateRequest(
            role=payload.role,
            content=payload.content,
            sender_name=sender_name,
        )
        message = await self._repository.add_message(
            empresa_id=empresa_id,
            conversation_id=conversation_id,
            payload=msg_payload,
        )

        conversation.asunto = conversation.asunto or payload.content[:80]
        conversation.estado = conversation.estado if conversation.estado != "closed" else "open"
        conversation.updated_at = datetime.now(UTC)
        await self._session.flush()

        ai_reply = None
        if payload.role == "client":
            self._typing.start_typing(str(conversation_id))
            try:
                response_text = await self._brain.generate_reply(
                    empresa_id=empresa_id,
                    user_message=payload.content,
                    conversation_id=conversation_id,
                )
            finally:
                self._typing.stop_typing(str(conversation_id))

            if response_text:
                ai_reply_db = MessageModel(
                    empresa_id=empresa_id,
                    conversation_id=conversation_id,
                    role="agent",
                    content=response_text,
                    sender_name="AI Asistente",
                )
                self._session.add(ai_reply_db)
                await self._session.flush()

                conversation.asunto = conversation.asunto or response_text[:80]
                ai_reply = MessageResponse.model_validate(MessageDTO.model_validate(ai_reply_db))

        await self._repository.commit()

        return ProcessMessageResponse(
            message=MessageResponse.model_validate(MessageDTO.model_validate(message)),
            ai_reply=ai_reply,
            typing=self._typing.get_state(str(conversation_id)),
        )

    async def regenerate_last_reply(
        self,
        *,
        empresa_id: UUID,
        conversation_id: UUID,
    ) -> MessageResponse | None:
        messages, _ = await self._repository.list_messages(
            empresa_id=empresa_id, conversation_id=conversation_id, limit=50, offset=0
        )
        if not messages:
            return None

        last_client_msg = None
        for m in reversed(messages):
            if m.role == "client":
                last_client_msg = m.content
                break

        if not last_client_msg:
            return None

        self._typing.start_typing(str(conversation_id))
        try:
            response_text = await self._brain.generate_reply(
                empresa_id=empresa_id,
                user_message=last_client_msg,
                conversation_id=conversation_id,
            )
        finally:
            self._typing.stop_typing(str(conversation_id))

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
