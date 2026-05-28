import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.classifiers.intent_classifier import IntentClassifierService
from app.ai.context.context_builder import ConversationContextBuilder
from app.ai.context.services.real_context_builder import RealContextBuilder
from app.ai.orchestrators.response_orchestrator import AIResponseOrchestrator
from app.ai.rules.sales_rules import SalesConversationRulesEngine
from app.ai.schemas.ai_schemas import (
    ClassifyRequest,
    ClassifyResponse,
    ContextRequest,
    ContextResponse,
    OrchestratorRequest,
    OrchestratorResponse,
    RichContextResponse,
)
from app.ai.services.llm_service import LLMService

logger = logging.getLogger("ai_sales_agent.ai.service")


class AIService:
    def __init__(
        self,
        llm_service: LLMService | None = None,
        session: AsyncSession | None = None,
    ) -> None:
        self._classifier = IntentClassifierService()
        self._context_builder = ConversationContextBuilder()
        self._rules_engine = SalesConversationRulesEngine()
        self._llm_service = llm_service
        self._session = session
        self._real_context_builder: RealContextBuilder | None = None
        if session is not None:
            self._real_context_builder = RealContextBuilder(session)
        self._orchestrator = AIResponseOrchestrator(
            classifier=self._classifier,
            context_builder=self._context_builder,
            rules_engine=self._rules_engine,
            llm_service=self._llm_service,
        )

    async def classify(self, request: ClassifyRequest) -> ClassifyResponse:
        classification = await self._classifier.classify(request.message)
        return ClassifyResponse(classification=classification)

    async def build_context(self, request: ContextRequest) -> ContextResponse:
        context = await self._context_builder.build(
            empresa_id=request.empresa_id,
            customer_id=request.customer_id,
            conversation_id=request.conversation_id,
        )
        return context

    async def build_rich_context(
        self,
        *,
        empresa_id: UUID,
        customer_id: UUID,
        conversation_id: UUID,
    ) -> RichContextResponse | None:
        if self._real_context_builder is None:
            return None
        rich = await self._real_context_builder.build_rich_context(
            empresa_id=empresa_id,
            customer_id=customer_id,
            conversation_id=conversation_id,
        )
        return RichContextResponse(context=rich)

    async def respond(self, request: OrchestratorRequest) -> OrchestratorResponse:
        rich_context = None
        if self._real_context_builder is not None:
            try:
                rich_context = await self._real_context_builder.build_rich_context(
                    empresa_id=request.empresa_id,
                    customer_id=request.customer_id,
                    conversation_id=request.conversation_id,
                )
            except Exception:
                logger.warning(
                    "Failed to build rich context for empresa=%s, conv=%s, falling back",
                    request.empresa_id, request.conversation_id,
                )
        return await self._orchestrator.orchestrate(
            request, rich_context=rich_context
        )
