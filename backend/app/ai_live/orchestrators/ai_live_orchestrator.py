import logging
from uuid import UUID

from app.ai_live.repository import ConversationAIRepository
from app.ai_live.services.handoff_service import HandoffService
from app.ai_live.services.insights_service import AIInsightsService
from app.ai_live.services.suggestions_service import AISuggestionsService


logger = logging.getLogger("ai_sales_agent.ai_live.orchestrator")


class AILiveOrchestrator:
    def __init__(
        self,
        repository: ConversationAIRepository,
        suggestions_service: AISuggestionsService,
        insights_service: AIInsightsService,
        handoff_service: HandoffService,
    ) -> None:
        self._repository = repository
        self._suggestions_service = suggestions_service
        self._insights_service = insights_service
        self._handoff_service = handoff_service

    async def process_new_message(
        self,
        *,
        empresa_id: UUID,
        conversation_id: UUID,
    ) -> None:
        state = await self._repository.get_or_create_state(
            empresa_id=empresa_id, conversation_id=conversation_id
        )
        if not state.ai_enabled or not state.auto_reply_enabled:
            return

        suggestions = await self._suggestions_service.suggest_replies(
            empresa_id=empresa_id,
            conversation_id=conversation_id,
        )
        if suggestions:
            await self._repository.update_state(
                state=state,
                ai_last_response=suggestions[0].text,
            )
