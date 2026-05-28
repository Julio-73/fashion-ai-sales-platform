import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.conversations.models import ConversationCore, MessageCore
from app.conversations.repository import ConversationCoreRepository
from app.modules.conversations.models import Conversation, Message
from app.modules.conversations.repository import ConversationRepository

logger = logging.getLogger("ai_sales_agent.shared_ai.conversation_adapter")


class ConversationAdapter:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._core_repo = ConversationCoreRepository(session)
        self._module_repo = ConversationRepository(session)

    async def get_adapter_type(
        self, *, empresa_id: UUID, conversation_id: UUID
    ) -> str:
        core = await self._core_repo.get_conversation_by_id(
            empresa_id=empresa_id, conversation_id=conversation_id
        )
        if core:
            return "core"
        module = await self._module_repo.get_conversation_by_id(
            empresa_id=empresa_id, conversation_id=conversation_id
        )
        if module:
            return "module"
        return "unknown"

    async def get_messages(
        self, *, empresa_id: UUID, conversation_id: UUID, limit: int = 50
    ) -> list[dict]:
        adapter_type = await self.get_adapter_type(
            empresa_id=empresa_id, conversation_id=conversation_id
        )
        if adapter_type == "core":
            msgs, _ = await self._core_repo.list_messages(
                empresa_id=empresa_id, conversation_id=conversation_id,
                limit=limit, offset=0,
            )
            return [
                {
                    "id": str(m.id),
                    "sender": m.sender,
                    "content": m.content,
                    "created_at": m.created_at,
                }
                for m in msgs
            ]
        if adapter_type == "module":
            msgs, _ = await self._module_repo.list_messages(
                empresa_id=empresa_id, conversation_id=conversation_id,
                limit=limit, offset=0,
            )
            return [
                {
                    "id": str(m.id),
                    "role": m.role,
                    "content": m.content,
                    "sender_name": m.sender_name,
                    "created_at": m.created_at,
                }
                for m in msgs
            ]
        return []

    async def get_customer_id(
        self, *, empresa_id: UUID, conversation_id: UUID
    ) -> UUID | None:
        core = await self._core_repo.get_conversation_by_id(
            empresa_id=empresa_id, conversation_id=conversation_id
        )
        if core:
            return core.customer_id
        module = await self._module_repo.get_conversation_by_id(
            empresa_id=empresa_id, conversation_id=conversation_id
        )
        if module:
            return module.cliente_id
        return None
