import logging
from enum import Enum

from app.ai.classifiers.intent_classifier import IntentClassifierService as AIIntentClassifier
from app.ai.schemas.ai_schemas import IntentType as AIIntentType
from app.sales.classifiers.intent_classifier import IntentClassifier as SalesIntentClassifier
from app.sales.intents.intent import IntentType as SalesIntentType

logger = logging.getLogger("ai_sales_agent.shared_ai.unified_intent")


class UnifiedIntentType(str, Enum):
    pricing = "pricing"
    purchase = "purchase"
    negotiation = "negotiation"
    delivery = "delivery"
    greeting = "greeting"
    support = "support"
    return_request = "return_request"
    product_question = "product_question"
    sizing = "sizing"
    product_interest = "product_interest"
    unknown = "unknown"


_INTENT_MAP_SALES_TO_UNIFIED: dict[SalesIntentType, UnifiedIntentType] = {
    SalesIntentType.pricing_intent: UnifiedIntentType.pricing,
    SalesIntentType.purchase_intent: UnifiedIntentType.purchase,
    SalesIntentType.negotiation_intent: UnifiedIntentType.negotiation,
    SalesIntentType.shipping_intent: UnifiedIntentType.delivery,
    SalesIntentType.support_intent: UnifiedIntentType.support,
    SalesIntentType.product_interest: UnifiedIntentType.product_interest,
    SalesIntentType.greeting: UnifiedIntentType.greeting,
    SalesIntentType.unknown: UnifiedIntentType.unknown,
}

_INTENT_MAP_AI_TO_UNIFIED: dict[AIIntentType, UnifiedIntentType] = {
    AIIntentType.pricing: UnifiedIntentType.pricing,
    AIIntentType.purchase_intent: UnifiedIntentType.purchase,
    AIIntentType.negotiation: UnifiedIntentType.negotiation,
    AIIntentType.delivery: UnifiedIntentType.delivery,
    AIIntentType.greeting: UnifiedIntentType.greeting,
    AIIntentType.support: UnifiedIntentType.support,
    AIIntentType.return_request: UnifiedIntentType.return_request,
    AIIntentType.product_question: UnifiedIntentType.product_question,
    AIIntentType.sizing: UnifiedIntentType.sizing,
    AIIntentType.unknown: UnifiedIntentType.unknown,
}


class UnifiedIntentService:
    def __init__(self) -> None:
        self._ai_classifier = AIIntentClassifier()
        self._sales_classifier = SalesIntentClassifier()

    def to_unified(self, intent) -> UnifiedIntentType:
        if isinstance(intent, SalesIntentType):
            return _INTENT_MAP_SALES_TO_UNIFIED.get(intent, UnifiedIntentType.unknown)
        if isinstance(intent, AIIntentType):
            return _INTENT_MAP_AI_TO_UNIFIED.get(intent, UnifiedIntentType.unknown)
        if isinstance(intent, str):
            try:
                sales_enum = SalesIntentType(intent)
                return _INTENT_MAP_SALES_TO_UNIFIED.get(sales_enum, UnifiedIntentType.unknown)
            except ValueError:
                pass
            try:
                ai_enum = AIIntentType(intent)
                return _INTENT_MAP_AI_TO_UNIFIED.get(ai_enum, UnifiedIntentType.unknown)
            except ValueError:
                pass
        return UnifiedIntentType.unknown

    def to_sales_type(self, unified: UnifiedIntentType) -> SalesIntentType:
        reverse = {v: k for k, v in _INTENT_MAP_SALES_TO_UNIFIED.items()}
        return reverse.get(unified, SalesIntentType.unknown)

    def to_ai_type(self, unified: UnifiedIntentType) -> AIIntentType:
        reverse = {v: k for k, v in _INTENT_MAP_AI_TO_UNIFIED.items()}
        return reverse.get(unified, AIIntentType.unknown)

    async def classify_unified(self, message: str) -> tuple[UnifiedIntentType, float]:
        ai_result = await self._ai_classifier.classify(message)
        unified = self.to_unified(ai_result.intent)
        return unified, ai_result.confidence

    def classify_unified_sync(self, message: str) -> tuple[UnifiedIntentType, int]:
        sales_type, weight = self._sales_classifier.classify(message)
        unified = self.to_unified(sales_type)
        return unified, weight

    def classify_all_unified(self, message: str) -> list[tuple[UnifiedIntentType, int]]:
        results = self._sales_classifier.classify_all(message)
        return [(self.to_unified(it), w) for it, w in results]
