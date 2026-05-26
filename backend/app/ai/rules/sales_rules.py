import logging
from uuid import UUID

from app.ai.schemas.ai_schemas import (
    ConversationStage,
    IntentType,
    SalesAction,
)

logger = logging.getLogger("ai_sales_agent.ai.rules")


class ConversationMetrics:
    def __init__(
        self,
        lead_score: float = 0.0,
        message_count: int = 0,
        has_previous_purchases: bool = False,
        has_requested_discount: bool = False,
        tags: list[str] | None = None,
    ) -> None:
        self.lead_score = lead_score
        self.message_count = message_count
        self.has_previous_purchases = has_previous_purchases
        self.has_requested_discount = has_requested_discount
        self.tags = tags or []


class SalesConversationRulesEngine:
    async def evaluate(
        self,
        *,
        empresa_id: UUID,
        intent: IntentType,
        stage: ConversationStage,
        lead_score: float,
        message_count: int,
        customer_tags: list[str] | None = None,
    ) -> SalesAction:
        metrics = ConversationMetrics(
            lead_score=lead_score,
            message_count=message_count,
            tags=customer_tags or [],
        )

        if intent == IntentType.return_request:
            return SalesAction.escalate

        if metrics.lead_score <= 0.2 and message_count >= 3:
            return SalesAction.follow_up

        if intent == IntentType.negotiation and metrics.lead_score >= 0.6:
            return SalesAction.suggest_discount

        if metrics.lead_score >= 0.8 and stage in (
            ConversationStage.active, ConversationStage.negotiation
        ):
            return SalesAction.suggest_upsell

        if intent == IntentType.purchase_intent and metrics.lead_score >= 0.5:
            return SalesAction.suggest_cross_sell

        if metrics.lead_score >= 0.7 and message_count >= 5:
            return SalesAction.escalate

        if metrics.lead_score <= 0.1 and message_count == 1:
            return SalesAction.follow_up

        return SalesAction.no_action
