import logging
from dataclasses import dataclass, field

from app.smart_sales.conversational_closer.acknowledgment_engine import AcknowledgmentEngine
from app.smart_sales.conversational_closer.contextual_response_engine import ContextualResponseEngine
from app.smart_sales.conversational_closer.intent_commitment_detector import (
    IntentCommitmentDetector, CommitmentResult, CommitmentLevel,
)
from app.smart_sales.conversational_closer.natural_language_variator import NaturalLanguageVariator
from app.smart_sales.conversational_closer.conversational_transition_engine import ConversationalTransitionEngine
from app.smart_sales.conversational_closer.objection_handler import ObjectionHandler
from app.smart_sales.conversational_closer.elite_sales_closer import EliteSalesCloser
from app.smart_sales.conversational_closer.emotional_conversation_engine import EmotionalConversationEngine
from app.smart_sales.conversational_closer.conversational_memory_enhancer import ConversationalMemoryEnhancer, ConversationMemoryState
from app.smart_sales.conversational_closer.human_conversation_rules import HumanConversationRules

logger = logging.getLogger("smart_sales.conversational_closer.engine")


@dataclass
class CloserInput:
    user_message: str = ""
    conversation_id: str = ""
    response: str = ""
    product_name: str = ""
    product_category: str = ""
    product_color: str = ""
    product_size: str = ""
    product_style: str = ""
    product_occasion: str = ""
    product_gender: str = ""
    total_stock: int = 0
    available_sizes: list[str] = field(default_factory=list)
    available_colors: list[str] = field(default_factory=list)
    emotional_state: str = ""
    sales_stage: str = ""
    has_product_history: bool = False
    confidence_level: str = ""


@dataclass
class CloserOutput:
    response: str = ""
    commitment: CommitmentResult | None = None
    was_objection: bool = False
    was_closing: bool = False
    was_gratitude: bool = False
    was_acknowledgment: bool = False
    memory_state: ConversationMemoryState | None = None


class ConversationalCloserEngine:
    def __init__(self) -> None:
        self._acknowledgment = AcknowledgmentEngine()
        self._contextual = ContextualResponseEngine()
        self._commitment = IntentCommitmentDetector()
        self._variator = NaturalLanguageVariator()
        self._transitions = ConversationalTransitionEngine()
        self._objections = ObjectionHandler()
        self._closer = EliteSalesCloser()
        self._emotional = EmotionalConversationEngine()
        self._memory = ConversationalMemoryEnhancer()
        self._rules = HumanConversationRules()

    @property
    def variator(self) -> NaturalLanguageVariator:
        return self._variator

    @property
    def transitions(self) -> ConversationalTransitionEngine:
        return self._transitions

    @property
    def memory(self) -> ConversationalMemoryEnhancer:
        return self._memory

    @property
    def contextual(self) -> ContextualResponseEngine:
        return self._contextual

    async def process(self, *, input_data: CloserInput) -> CloserOutput:
        output = CloserOutput()
        msg = input_data.user_message

        memory_state = self._memory.update(
            conversation_id=input_data.conversation_id,
            message=msg,
            product_name=input_data.product_name,
            product_category=input_data.product_category,
            color=input_data.product_color,
            size=input_data.product_size,
            style=input_data.product_style,
            occasion=input_data.product_occasion,
            gender=input_data.product_gender,
            intent=input_data.sales_stage,
            mood=input_data.emotional_state,
            confidence=input_data.confidence_level,
        )
        output.memory_state = memory_state

        commitment = self._commitment.detect(msg, input_data.has_product_history)
        output.commitment = commitment

        self._contextual.update_snapshot(
            conversation_id=input_data.conversation_id,
            message=msg,
            commitment=commitment,
            product_name=input_data.product_name,
            product_category=input_data.product_category,
            color=input_data.product_color,
            size=input_data.product_size,
            style=input_data.product_style,
            occasion=input_data.product_occasion,
            gender=input_data.product_gender,
        )

        was_objection, objection_response = self._objections.handle_objection(msg)
        if was_objection:
            output.was_objection = True
            output.response = objection_response
            return output

        if self._acknowledgment.is_gratitude(msg):
            output.was_gratitude = True
            output.response = self._build_gratitude_response(input_data)
            return output

        if self._acknowledgment.is_ok_acknowledgment(msg):
            output.was_acknowledgment = True
            output.response = self._build_ok_response(input_data)
            return output

        if self._acknowledgment.is_hesitation(msg):
            output.response = self._build_hesitation_response(input_data)
            return output

        if commitment.level in (CommitmentLevel.committed, CommitmentLevel.ready_to_buy):
            output.was_closing = True
            output.response = self._build_closing_response(input_data, commitment)
            return output

        if commitment.level == CommitmentLevel.interested and input_data.response:
            output.response = self._enhance_response(input_data)
            return output

        output.response = input_data.response
        return output

    def _build_gratitude_response(self, ctx: CloserInput) -> str:
        ack = self._acknowledgment.get_gratitude_response()
        transition = self._transitions.get_transition(ctx.user_message, ctx.product_category)
        styling = ""
        if ctx.product_name and ctx.product_category:
            styling = "\n\nSi quieres, puedo ayudarte a armar el outfit completo 🔥"

        parts = [ack]
        if ctx.product_name:
            parts.append(f"{ctx.product_name} {'en ' + ctx.product_color if ctx.product_color else ''}{' talla ' + ctx.product_size if ctx.product_size else ''} sí está disponible.")
        if transition:
            parts.append(transition)
        if styling:
            parts.append(styling)
        parts.append("¿Algo más en que pueda ayudarte? 👌")
        return "\n\n".join(parts)

    def _build_ok_response(self, ctx: CloserInput) -> str:
        ack = self._acknowledgment.get_ok_response()
        transition = self._transitions.get_transition(ctx.user_message, ctx.product_category)
        parts = [ack]
        if transition:
            parts.append(transition)
        if ctx.product_name:
            parts.append(f"Recuerda que {ctx.product_name} está disponible.")
        parts.append("¿Necesitas algo más? 😊")
        return "\n\n".join(parts)

    def _build_hesitation_response(self, ctx: CloserInput) -> str:
        snap = self._contextual.get_snapshot(ctx.conversation_id)
        if snap.product_already_shown:
            return "Tranqui 😊 Si quieres puedo mostrarte opciones similares para que compares estilos, precios y fits antes de decidir 👌"
        return "Sin problema. Cuéntame más qué estás buscando y te ayudo a encontrar justo lo que necesitas 🔥"

    def _build_closing_response(self, ctx: CloserInput, commitment: CommitmentResult) -> str:
        has_size = bool(ctx.product_size or commitment.detected_size)
        has_color = bool(ctx.product_color or commitment.detected_color)
        return self._closer.build_closing(
            product_name=ctx.product_name or commitment.detected_product,
            product_category=ctx.product_category,
            available_sizes=ctx.available_sizes,
            available_colors=ctx.available_colors,
            has_size=has_size,
            has_color=has_color,
            total_stock=ctx.total_stock,
        )

    def _enhance_response(self, ctx: CloserInput) -> str:
        opening = self._variator.get_opening()
        closing = self._variator.get_closing()
        tone = self._emotional.get_tone_for_emotion(ctx.emotional_state)
        response = self._emotional.apply_tone(ctx.response, tone)
        return f"{opening} {response} {closing}"
