from dataclasses import dataclass

from app.smart_sales.conversational_closer.acknowledgment_engine import AcknowledgmentEngine
from app.smart_sales.conversational_closer.intent_commitment_detector import CommitmentResult


@dataclass
class ContextSnapshot:
    has_product_history: bool = False
    last_product_name: str = ""
    last_product_category: str = ""
    last_color: str = ""
    last_size: str = ""
    last_style: str = ""
    last_occasion: str = ""
    last_gender: str = ""
    last_intent: str = ""
    message_count: int = 0
    product_already_shown: bool = False
    already_asked_size: bool = False
    already_asked_color: bool = False


class ContextualResponseEngine:
    def __init__(self) -> None:
        self._acknowledgment = AcknowledgmentEngine()
        self._conversations: dict[str, ContextSnapshot] = {}

    def get_snapshot(self, conversation_id: str) -> ContextSnapshot:
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = ContextSnapshot()
        return self._conversations[conversation_id]

    def update_snapshot(
        self,
        conversation_id: str,
        message: str,
        commitment: CommitmentResult | None = None,
        product_name: str = "",
        product_category: str = "",
        color: str = "",
        size: str = "",
        style: str = "",
        occasion: str = "",
        gender: str = "",
    ) -> ContextSnapshot:
        snap = self.get_snapshot(conversation_id)
        snap.message_count += 1

        if product_name:
            snap.last_product_name = product_name
            snap.product_already_shown = True
        if product_category:
            snap.last_product_category = product_category
        if color:
            snap.last_color = color
        if size:
            snap.last_size = size
        if style:
            snap.last_style = style
        if occasion:
            snap.last_occasion = occasion
        if gender:
            snap.last_gender = gender

        if commitment:
            snap.last_intent = commitment.level.value
            if commitment.detected_size:
                snap.last_size = commitment.detected_size
                snap.already_asked_size = True
            if commitment.detected_color:
                snap.last_color = commitment.detected_color
                snap.already_asked_color = True

        return snap

    def should_relist_products(self, conversation_id: str) -> bool:
        snap = self.get_snapshot(conversation_id)
        if not snap.product_already_shown:
            return True
        if snap.message_count <= 1:
            return True
        return False

    def should_suggest_styling(self, conversation_id: str) -> bool:
        snap = self.get_snapshot(conversation_id)
        return snap.product_already_shown and snap.message_count >= 1
