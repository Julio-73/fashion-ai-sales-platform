from dataclasses import dataclass, field


@dataclass
class ConversationMemoryState:
    product_name: str = ""
    product_category: str = ""
    color: str = ""
    size: str = ""
    style: str = ""
    occasion: str = ""
    gender: str = ""
    last_intent: str = ""
    last_mood: str = ""
    last_product_shown: str = ""
    confidence_level: str = ""
    current_outfit_context: str = ""
    suggested_products: list[str] = field(default_factory=list)
    message_count: int = 0
    follow_up_count: int = 0
    closing_attempted: bool = False
    upsell_offered: bool = False


class ConversationalMemoryEnhancer:
    def __init__(self) -> None:
        self._memories: dict[str, ConversationMemoryState] = {}

    def get_state(self, conversation_id: str) -> ConversationMemoryState:
        if conversation_id not in self._memories:
            self._memories[conversation_id] = ConversationMemoryState()
        return self._memories[conversation_id]

    def update(
        self,
        conversation_id: str,
        message: str = "",
        product_name: str = "",
        product_category: str = "",
        color: str = "",
        size: str = "",
        style: str = "",
        occasion: str = "",
        gender: str = "",
        intent: str = "",
        mood: str = "",
        confidence: str = "",
    ) -> ConversationMemoryState:
        state = self.get_state(conversation_id)
        state.message_count += 1

        if product_name:
            state.product_name = product_name
            state.last_product_shown = product_name
        if product_category:
            state.product_category = product_category
        if color:
            state.color = color
        if size:
            state.size = size
        if style:
            state.style = style
        if occasion:
            state.occasion = occasion
        if gender:
            state.gender = gender
        if intent:
            state.last_intent = intent
        if mood:
            state.last_mood = mood
        if confidence:
            state.confidence_level = confidence

        return state

    def get_context_summary(self, conversation_id: str) -> str:
        state = self.get_state(conversation_id)
        parts = []
        if state.product_name:
            parts.append(f"Producto: {state.product_name}")
        if state.product_category:
            parts.append(f"Categoría: {state.product_category}")
        if state.color:
            parts.append(f"Color: {state.color}")
        if state.size:
            parts.append(f"Tall: {state.size}")
        if state.style:
            parts.append(f"Estilo: {state.style}")
        if state.occasion:
            parts.append(f"Ocasión: {state.occasion}")
        if state.last_intent:
            parts.append(f"Intención: {state.last_intent}")
        if parts:
            return " | ".join(parts)
        return "Sin contexto previo"
