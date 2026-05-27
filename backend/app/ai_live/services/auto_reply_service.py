import logging
from uuid import UUID

from app.ai_live.repository import ConversationAIRepository
from app.conversations.models import MessageCore
from app.conversations.repository import ConversationCoreRepository
from app.conversations.schemas import MessageCoreCreateRequest
from app.modules.conversations.schemas import MessageCreateRequest
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("ai_sales_agent.ai_live.auto_reply")


class AIReplyService:
    def __init__(
        self,
        session: AsyncSession,
        ai_live_repo: ConversationAIRepository,
    ) -> None:
        self._session = session
        self._ai_live_repo = ai_live_repo

    async def should_auto_reply(
        self,
        *,
        empresa_id: UUID,
        conversation_id: UUID,
        sender: str,
        status: str,
    ) -> bool:
        if sender != "client" and sender != "user":
            return False
        if status == "closed":
            return False
        state = await self._ai_live_repo.get_or_create_state(
            empresa_id=empresa_id, conversation_id=conversation_id
        )
        if not state.ai_enabled or not state.auto_reply_enabled:
            return False
        if state.escalation_required:
            return False
        return True

    async def generate_and_save_ai_reply(
        self,
        *,
        empresa_id: UUID,
        conversation_id: UUID,
        user_message: str,
    ) -> MessageCore | None:
        from app.ai.services.ai_service import AIService

        ai_service = AIService()
        await self._ai_live_repo.add_event(
            empresa_id=empresa_id,
            conversation_id=conversation_id,
            event_type="ai_response_started",
            payload={"user_message": user_message[:200]},
        )

        try:
            result = await ai_service.respond(
                __import__("app.ai.schemas.ai_schemas", fromlist=["OrchestratorRequest"]).OrchestratorRequest(
                    message=user_message,
                    empresa_id=empresa_id,
                    customer_id=UUID(int=0),
                    conversation_id=conversation_id,
                )
            )
        except Exception:
            logger.exception("AI response generation failed for conversation=%s", conversation_id)
            await self._ai_live_repo.add_event(
                empresa_id=empresa_id,
                conversation_id=conversation_id,
                event_type="ai_response_failed",
                payload={"user_message": user_message[:200]},
            )
            return None

        if not result.should_reply or not result.generated_response:
            return None

        ai_content = result.generated_response
        ai_message = MessageCore(
            empresa_id=empresa_id,
            conversation_id=conversation_id,
            sender="bot",
            content=ai_content,
        )
        self._session.add(ai_message)
        await self._session.flush()

        await self._ai_live_repo.add_event(
            empresa_id=empresa_id,
            conversation_id=conversation_id,
            event_type="ai_response_generated",
            payload={
                "content_preview": ai_content[:200],
                "intent": result.intent.value,
                "confidence": result.intent_confidence,
            },
        )

        try:
            await self._ai_live_repo.update_state(
                state=await self._ai_live_repo.get_or_create_state(
                    empresa_id=empresa_id, conversation_id=conversation_id,
                ),
                last_detected_intent=result.intent.value,
                ai_confidence=result.intent_confidence,
                ai_last_response=ai_content,
            )
        except Exception:
            logger.warning("Failed to update AI state for conversation=%s", conversation_id)

        return ai_message
