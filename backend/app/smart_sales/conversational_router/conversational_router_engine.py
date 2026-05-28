import logging
from dataclasses import dataclass, field

from .conversational_intent_detector import ConversationalIntent, ConversationalIntentDetector, IntentResult
from .greeting_handler import get_greeting
from .gratitude_handler import get_gratitude_response
from .hesitation_handler import get_hesitation_response
from .casual_conversation_handler import get_casual_response
from .conversational_state_router import (
    ConversationalStateRouter,
    ConversationStage,
    StateTransitionResult,
)
from .human_response_guard import HumanResponseGuard

logger = logging.getLogger("ai_sales_agent.smart_sales.conversational_router")


@dataclass
class RouterResult:
    handled: bool = False
    response: str = ""
    intent: ConversationalIntent = ConversationalIntent.unknown
    confidence: float = 0.0
    stage: ConversationStage = ConversationStage.greeting
    transition: StateTransitionResult | None = None
    detected_entities: dict[str, str] = field(default_factory=dict)


HANDLED_INTENTS: set[ConversationalIntent] = {
    ConversationalIntent.greeting,
    ConversationalIntent.gratitude,
    ConversationalIntent.hesitation,
    ConversationalIntent.casual_chat,
}

MIN_CONFIDENCE: float = 0.6


class ConversationalRouterEngine:
    def __init__(self) -> None:
        self._detector = ConversationalIntentDetector()
        self._state_router = ConversationalStateRouter()
        self._response_guard = HumanResponseGuard()

    def process(
        self,
        message: str,
        conversation_id: str | None = None,
        gender: str | None = None,
        force_refresh: bool = False,
    ) -> RouterResult:
        result = RouterResult()

        if not message or not message.strip():
            return result

        cid = conversation_id or "__global__"

        intent_result: IntentResult = self._detector.detect(message)
        result.intent = intent_result.intent
        result.confidence = intent_result.confidence
        result.detected_entities = intent_result.detected_entities

        stage = self._state_router.get_stage(cid)
        result.stage = stage

        if intent_result.confidence < MIN_CONFIDENCE:
            return result

        if intent_result.intent not in HANDLED_INTENTS:
            return result

        transition = self._state_router.transition(cid, intent_result.intent)
        result.transition = transition

        response = self._build_response(intent_result.intent, cid, gender)

        guard_check = self._response_guard.check_response(cid, response)
        if guard_check.is_blocked:
            logger.warning(
                "Response blocked by guard for %s: %s (score=%.2f)",
                cid, guard_check.block_reason, guard_check.total_score,
            )
            backup = self._build_fallback_response(intent_result.intent, cid)
            response = backup
            guard_check2 = self._response_guard.check_response(cid, backup)
            if guard_check2.is_blocked:
                return result

        self._response_guard.record_response(cid, response)
        result.handled = True
        result.response = response

        return result

    def _build_response(
        self,
        intent: ConversationalIntent,
        conversation_id: str,
        gender: str | None = None,
    ) -> str:
        if intent == ConversationalIntent.greeting:
            return get_greeting(conversation_id, gender)
        elif intent == ConversationalIntent.gratitude:
            return get_gratitude_response(conversation_id)
        elif intent == ConversationalIntent.hesitation:
            return get_hesitation_response(conversation_id)
        elif intent == ConversationalIntent.casual_chat:
            return get_casual_response(conversation_id)
        return ""

    def _build_fallback_response(
        self,
        intent: ConversationalIntent,
        conversation_id: str,
    ) -> str:
        if intent == ConversationalIntent.greeting:
            return "¡Hola! 😊 ¿En qué puedo ayudarte hoy?"
        elif intent == ConversationalIntent.gratitude:
            return "Con gusto 😊 Cuando necesites algo más, acá estoy!"
        elif intent == ConversationalIntent.hesitation:
            return "Tómate tu tiempo 😊 Cuando quieras, acá estoy."
        elif intent == ConversationalIntent.casual_chat:
            return "Genial 😊 ¿Algo más en que pueda ayudarte?"
        return ""

    def record_response(self, conversation_id: str, response: str) -> None:
        self._response_guard.record_response(conversation_id, response)

    def get_state_router(self) -> ConversationalStateRouter:
        return self._state_router

    def get_response_guard(self) -> HumanResponseGuard:
        return self._response_guard

    def reset(self, conversation_id: str) -> None:
        self._state_router.reset(conversation_id)
        self._response_guard.reset(conversation_id)
