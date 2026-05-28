import logging
from uuid import UUID

from app.ai.rules.sales_rules import SalesConversationRulesEngine as AIRulesEngine
from app.ai.schemas.ai_schemas import (
    ConversationStage,
    IntentType as AIIntentType,
    SalesAction as AISalesAction,
)
from app.sales.rules.sales_rules import SalesRulesEngine as SalesRulesEngine_
from app.shared_ai.unified_intent_service import UnifiedIntentService, UnifiedIntentType

logger = logging.getLogger("ai_sales_agent.shared_ai.unified_rules")


class UnifiedRulesEngine:
    def __init__(self) -> None:
        self._ai_rules = AIRulesEngine()
        self._sales_rules = SalesRulesEngine_()
        self._intent_service = UnifiedIntentService()

    async def evaluate_ai_action(
        self,
        *,
        empresa_id: UUID,
        intent: AIIntentType | UnifiedIntentType,
        stage: ConversationStage,
        lead_score: float,
        message_count: int,
        customer_tags: list[str] | None = None,
    ) -> AISalesAction:
        if isinstance(intent, UnifiedIntentType):
            intent = self._intent_service.to_ai_type(intent)
        return await self._ai_rules.evaluate(
            empresa_id=empresa_id,
            intent=intent,
            stage=stage,
            lead_score=lead_score,
            message_count=message_count,
            customer_tags=customer_tags,
        )

    def evaluate_sales_rules(self, rule_context) -> list:
        return self._sales_rules.evaluate_all(rule_context)
