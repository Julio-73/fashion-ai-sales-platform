import logging

from app.ai.classifiers.intent_classifier import IntentClassifierService
from app.ai.context.context_builder import ConversationContextBuilder
from app.ai.orchestrators.response_orchestrator import AIResponseOrchestrator
from app.ai.rules.sales_rules import SalesConversationRulesEngine
from app.ai.schemas.ai_schemas import (
    ClassifyRequest,
    ClassifyResponse,
    ContextRequest,
    ContextResponse,
    OrchestratorRequest,
    OrchestratorResponse,
)
from app.ai.services.llm_service import LLMService

logger = logging.getLogger("ai_sales_agent.ai.service")


class AIService:
    def __init__(self, llm_service: LLMService | None = None) -> None:
        self._classifier = IntentClassifierService()
        self._context_builder = ConversationContextBuilder()
        self._rules_engine = SalesConversationRulesEngine()
        self._llm_service = llm_service
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

    async def respond(self, request: OrchestratorRequest) -> OrchestratorResponse:
        return await self._orchestrator.orchestrate(request)
