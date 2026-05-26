import logging

from app.ai.classifiers.intent_classifier import IntentClassifierService
from app.ai.context.context_builder import ConversationContextBuilder
from app.ai.orchestrators.response_templates import ResponseTemplateBuilder
from app.ai.rules.sales_rules import SalesConversationRulesEngine
from app.ai.schemas.ai_schemas import (
    OrchestratorRequest,
    OrchestratorResponse,
    ReplyType,
    SalesAction,
)

logger = logging.getLogger("ai_sales_agent.ai.orchestrator")


class AIResponseOrchestrator:
    def __init__(
        self,
        classifier: IntentClassifierService | None = None,
        context_builder: ConversationContextBuilder | None = None,
        rules_engine: SalesConversationRulesEngine | None = None,
    ) -> None:
        self._classifier = classifier or IntentClassifierService()
        self._context_builder = context_builder or ConversationContextBuilder()
        self._rules_engine = rules_engine or SalesConversationRulesEngine()

    async def orchestrate(self, request: OrchestratorRequest) -> OrchestratorResponse:
        classification = await self._classifier.classify(request.message)
        context = await self._context_builder.build(
            empresa_id=request.empresa_id,
            customer_id=request.customer_id,
            conversation_id=request.conversation_id,
        )

        sales_action = await self._rules_engine.evaluate(
            empresa_id=request.empresa_id,
            intent=classification.intent,
            stage=context.context.conversation_stage,
            lead_score=context.context.customer.lead_score,
            message_count=len(context.context.recent_messages),
            customer_tags=context.context.customer.tags,
        )

        return self._build_response(
            classification.intent,
            classification.confidence,
            sales_action,
            context.context.customer.customer_name,
        )

    def _build_response(
        self,
        intent,
        confidence: float,
        sales_action: SalesAction,
        customer_name: str,
    ) -> OrchestratorResponse:
        reply_type = ResponseTemplateBuilder.get_reply_type(intent)
        should_reply = reply_type != ReplyType.no_reply
        generated = ""
        escalate_reason: str | None = None
        discount_pct: float | None = None

        if sales_action == SalesAction.escalate:
            generated = ResponseTemplateBuilder.ESCALATION_NOTICE
            escalate_reason = f"Escalado por acción: {sales_action.value}, intent: {intent.value}"
            reply_type = ReplyType.escalation
        elif sales_action == SalesAction.follow_up:
            generated = ResponseTemplateBuilder.build_follow_up(customer_name)
            reply_type = ReplyType.follow_up
        elif sales_action == SalesAction.suggest_discount:
            generated = ResponseTemplateBuilder.build_sales_response(intent)
            discount_pct = 10.0
        elif sales_action == SalesAction.suggest_cross_sell:
            generated = ResponseTemplateBuilder.build_cross_sell()
        elif reply_type == ReplyType.support:
            generated = ResponseTemplateBuilder.build_support_response(intent)
        elif reply_type == ReplyType.sales:
            generated = ResponseTemplateBuilder.build_sales_response(intent)
        elif reply_type == ReplyType.greeting:
            generated = ResponseTemplateBuilder.build_sales_response(intent)

        return OrchestratorResponse(
            intent=intent,
            intent_confidence=confidence,
            sales_action=sales_action,
            should_reply=should_reply,
            reply_type=reply_type,
            generated_response=generated,
            suggested_discount_pct=discount_pct,
            escalate_reason=escalate_reason,
        )
