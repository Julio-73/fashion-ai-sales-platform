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

logger = logging.getLogger("ai_sales_agent.ai.service")


class AIService:
    def __init__(self) -> None:
        self._classifier = IntentClassifierService()
        self._context_builder = ConversationContextBuilder()
        self._rules_engine = SalesConversationRulesEngine()
        self._orchestrator = AIResponseOrchestrator(
            classifier=self._classifier,
            context_builder=self._context_builder,
            rules_engine=self._rules_engine,
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
