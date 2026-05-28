import logging

from app.ai.classifiers.intent_classifier import IntentClassifierService
from app.ai.context.context_builder import ConversationContextBuilder
from app.ai.orchestrators.response_templates import ResponseTemplateBuilder
from app.ai.rules.sales_rules import SalesConversationRulesEngine
from app.ai.schemas.ai_schemas import (
    OrchestratorRequest,
    OrchestratorResponse,
    ReplyType,
    RichContextData,
    SalesAction,
)
from app.ai.services.llm_service import LLMService

logger = logging.getLogger("ai_sales_agent.ai.orchestrator")


class AIResponseOrchestrator:
    def __init__(
        self,
        classifier: IntentClassifierService | None = None,
        context_builder: ConversationContextBuilder | None = None,
        rules_engine: SalesConversationRulesEngine | None = None,
        llm_service: LLMService | None = None,
    ) -> None:
        self._classifier = classifier or IntentClassifierService()
        self._context_builder = context_builder or ConversationContextBuilder()
        self._rules_engine = rules_engine or SalesConversationRulesEngine()
        self._llm_service = llm_service

    async def orchestrate(
        self,
        request: OrchestratorRequest,
        rich_context: RichContextData | None = None,
    ) -> OrchestratorResponse:
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

        return await self._build_response(
            empresa_id=request.empresa_id,
            intent=classification.intent,
            confidence=classification.confidence,
            sales_action=sales_action,
            customer_name=context.context.customer.customer_name,
            context_data=context.context,
            user_message=request.message,
            rich_context=rich_context,
        )

    async def _build_response(
        self,
        *,
        empresa_id,
        intent,
        confidence: float,
        sales_action: SalesAction,
        customer_name: str,
        context_data,
        user_message: str,
        rich_context: RichContextData | None = None,
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
        elif sales_action == SalesAction.suggest_discount:
            discount_pct = 10.0

        if not generated and self._llm_service and self._llm_service.is_configured:
            llm_context = context_data
            if rich_context:
                llm_context = rich_context
            generated = await self._llm_service.generate_response(
                empresa_id=empresa_id,
                intent=intent,
                sales_action=sales_action,
                context=llm_context,
                user_message=user_message,
            )

        if not generated:
            if sales_action == SalesAction.follow_up:
                generated = ResponseTemplateBuilder.build_follow_up(customer_name)
                reply_type = ReplyType.follow_up
            elif sales_action == SalesAction.suggest_cross_sell:
                generated = ResponseTemplateBuilder.build_cross_sell()
            elif reply_type == ReplyType.support:
                generated = ResponseTemplateBuilder.build_support_response(intent)
            elif reply_type in (ReplyType.sales, ReplyType.greeting):
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
            rich_context=rich_context,
        )
