import logging
from dataclasses import dataclass

from app.smart_sales.human_sales.emotional_detector import EmotionalDetector, EmotionalResult
from app.smart_sales.human_sales.conversational_flow_engine import ConversationalFlowEngine, SalesStage
from app.smart_sales.human_sales.sales_psychology_engine import SalesPsychologyEngine, SalesPsychologyContext
from app.smart_sales.human_sales.personality_engine import PersonalityEngine
from app.smart_sales.human_sales.styling_advisor import StylingAdvisor, StylingAdvice
from app.smart_sales.human_sales.closing_engine import ClosingEngine, ClosingContext
from app.smart_sales.human_sales.tone_profiles import ToneProfile

logger = logging.getLogger("smart_sales.human_sales.engine")


@dataclass
class HumanSalesInput:
    user_message: str = ""
    empresa_id: str = ""
    conversation_id: str = ""
    customer_id: str = ""
    product_name: str = ""
    product_category: str = ""
    product_color: str = ""
    product_style: str = ""
    product_occasion: str = ""
    product_gender: str = ""
    product_size: str = ""
    total_stock: int = 0
    is_high_demand: bool = False
    is_seasonal: bool = False
    confidence_level: str = ""
    response: str = ""


@dataclass
class HumanSalesOutput:
    enhanced_response: str = ""
    emotional: EmotionalResult | None = None
    personality_profile: ToneProfile | None = None
    sales_psychology: SalesPsychologyContext | None = None
    closing: ClosingContext | None = None
    styling: StylingAdvice | None = None
    current_stage: SalesStage = SalesStage.greeting


class HumanSalesPsychologyEngine:
    def __init__(self) -> None:
        self._emotional_detector = EmotionalDetector()
        self._personality_engine = PersonalityEngine()
        self._sales_psychology = SalesPsychologyEngine()
        self._closing_engine = ClosingEngine()
        self._styling_advisor = StylingAdvisor()
        self._flow_engine = ConversationalFlowEngine()

    @property
    def emotional_detector(self) -> EmotionalDetector:
        return self._emotional_detector

    @property
    def personality(self) -> PersonalityEngine:
        return self._personality_engine

    @property
    def sales_psychology(self) -> SalesPsychologyEngine:
        return self._sales_psychology

    @property
    def closing(self) -> ClosingEngine:
        return self._closing_engine

    @property
    def styling(self) -> StylingAdvisor:
        return self._styling_advisor

    @property
    def flow(self) -> ConversationalFlowEngine:
        return self._flow_engine

    async def process(
        self,
        *,
        input_data: HumanSalesInput,
    ) -> HumanSalesOutput:
        output = HumanSalesOutput()

        emotional = self._emotional_detector.detect(input_data.user_message)
        output.emotional = emotional

        stage = self._flow_engine.update_stage(
            input_data.conversation_id,
            input_data.user_message,
            emotional.state.value if emotional else None,
        )
        output.current_stage = stage

        profile = self._personality_engine.detect_profile(
            style=input_data.product_style or None,
            category=input_data.product_category or None,
            gender=input_data.product_gender or None,
        )
        output.personality_profile = profile

        psych = self._sales_psychology.build_context(
            product_category=input_data.product_category or None,
            total_stock=input_data.total_stock,
            is_high_demand=input_data.is_high_demand,
            is_seasonal=input_data.is_seasonal,
            is_high_intent=emotional.state == "high_intent" if emotional else False,
            emotional_state=emotional.state.value if emotional else None,
            sales_stage=stage.value if stage else "",
            conversation_id=input_data.conversation_id,
        )
        output.sales_psychology = psych

        if input_data.total_stock > 0:
            styling_advice = self._styling_advisor.get_styling_advice(
                category=input_data.product_category or None,
                color=input_data.product_color or None,
                occasion=input_data.product_occasion or None,
            )
            output.styling = styling_advice

        if self._closing_engine.should_attempt_close(input_data.user_message):
            close = self._closing_engine.build_closing(
                product_name=input_data.product_name,
                already_has_size=bool(input_data.product_size),
                already_has_color=bool(input_data.product_color),
            )
            output.closing = close
            self._flow_engine.mark_closing_initiated(input_data.conversation_id)

        enhanced = self._enrich_response(
            original=input_data.response,
            output=output,
        )
        output.enhanced_response = enhanced

        return output

    def _enrich_response(
        self,
        original: str,
        output: HumanSalesOutput,
    ) -> str:
        if not original:
            return original

        if output.closing and output.closing.should_close:
            return self._apply_closing(output.closing, original)

        result = original

        parts = [result]

        if output.styling and output.styling.should_use:
            parts.append(output.styling.advice)

        if output.sales_psychology:
            sp = output.sales_psychology
            if sp.social_proof:
                parts.append(sp.social_proof)
            if sp.scarcity:
                parts.append(sp.scarcity)
            if sp.urgency:
                parts.append(sp.urgency)
            if sp.persuasion_emotional:
                parts.append(sp.persuasion_emotional)

        return "\n\n".join(parts)

    def _apply_closing(self, ctx: ClosingContext, response: str) -> str:
        opener = ctx.opener or "Perfecto"
        confirmation = ctx.confirmation or ""

        parts = [opener]

        if confirmation:
            parts.append(confirmation)

        if ctx.size_question:
            parts.append(ctx.size_question)
        elif ctx.color_question:
            parts.append(ctx.color_question)

        if ctx.delivery_question:
            parts.append(ctx.delivery_question)

        if ctx.closer:
            parts.append(ctx.closer)

        return "\n\n".join(parts)

    def reset_conversation(self, conversation_id: str) -> None:
        self._sales_psychology.social_proof.reset(conversation_id)
        self._sales_psychology.scarcity.reset(conversation_id)
        self._sales_psychology.urgency.reset(conversation_id)
        self._sales_psychology.persuasion.reset(conversation_id)
