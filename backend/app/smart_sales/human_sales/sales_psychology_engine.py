import logging
from dataclasses import dataclass, field

from app.smart_sales.human_sales.social_proof_engine import SocialProofEngine
from app.smart_sales.human_sales.scarcity_engine import ScarcityEngine
from app.smart_sales.human_sales.urgency_engine import UrgencyEngine
from app.smart_sales.human_sales.persuasion_engine import PersuasionEngine
from app.smart_sales.human_sales.closing_engine import ClosingEngine
from app.smart_sales.human_sales.styling_advisor import StylingAdvisor

logger = logging.getLogger("smart_sales.human_sales.sales_psychology")


@dataclass
class SalesPsychologyContext:
    social_proof: str = ""
    scarcity: str = ""
    urgency: str = ""
    persuasion_reassurance: str = ""
    persuasion_confidence: str = ""
    persuasion_premium: str = ""
    persuasion_emotional: str = ""
    styling: str = ""
    closing_approach: str = ""
    active_techniques: list[str] = field(default_factory=list)


class SalesPsychologyEngine:
    def __init__(self) -> None:
        self._social_proof = SocialProofEngine()
        self._scarcity = ScarcityEngine()
        self._urgency = UrgencyEngine()
        self._persuasion = PersuasionEngine()
        self._closing = ClosingEngine()
        self._styling = StylingAdvisor()

    @property
    def social_proof(self) -> SocialProofEngine:
        return self._social_proof

    @property
    def scarcity(self) -> ScarcityEngine:
        return self._scarcity

    @property
    def urgency(self) -> UrgencyEngine:
        return self._urgency

    @property
    def persuasion(self) -> PersuasionEngine:
        return self._persuasion

    @property
    def closing(self) -> ClosingEngine:
        return self._closing

    @property
    def styling(self) -> StylingAdvisor:
        return self._styling

    def build_context(
        self,
        *,
        product_category: str | None = None,
        total_stock: int = 0,
        is_high_demand: bool = False,
        is_seasonal: bool = False,
        is_high_intent: bool = False,
        emotional_state: str | None = None,
        sales_stage: str = "",
        conversation_id: str = "",
    ) -> SalesPsychologyContext:
        ctx = SalesPsychologyContext()

        proof = self._social_proof.get_proof(product_category, conversation_id)
        if proof:
            ctx.social_proof = proof
            ctx.active_techniques.append("social_proof")

        scarc = self._scarcity.evaluate(
            total_stock=total_stock,
            is_high_demand=is_high_demand,
            is_seasonal=is_seasonal,
            conversation_id=conversation_id,
        )
        if scarc.should_use:
            ctx.scarcity = scarc.phrase
            ctx.active_techniques.append("scarcity")

        urg = self._urgency.evaluate(
            total_stock=total_stock,
            is_high_intent=is_high_intent,
            stage=sales_stage,
            conversation_id=conversation_id,
        )
        if urg.should_use:
            ctx.urgency = urg.phrase
            ctx.active_techniques.append("urgency")

        if sales_stage in ("persuasion", "closing", "upsell"):
            pers = self._persuasion.build_persuasion(conversation_id)
            if pers.should_use:
                ctx.persuasion_reassurance = pers.reassurance
                ctx.persuasion_confidence = pers.confidence
                ctx.persuasion_premium = pers.premium_perception
                ctx.persuasion_emotional = pers.emotional
                ctx.active_techniques.extend(["reassurance", "confidence"])

        return ctx
