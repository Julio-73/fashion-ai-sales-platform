import logging
from dataclasses import dataclass, field
from uuid import UUID

logger = logging.getLogger("ai_sales_agent.smart_sales.memory")


@dataclass
class ConversationContext:
    last_product_type: str | None = None
    last_color: str | None = None
    last_size: str | None = None
    last_gender: str | None = None
    last_style: str | None = None
    last_occasion: str | None = None
    last_intent: str | None = None
    last_product_id: str | None = None
    last_product_name: str | None = None
    repeated_intent: int = 0
    recent_messages: list[str] = field(default_factory=list)
    recent_entities: list[dict] = field(default_factory=list)
    follow_up_count: int = 0
    last_confidence: float = 0.0
    suggested_products: set[str] = field(default_factory=set)

    def update_from_message(self, message: str, entities: dict | None = None) -> None:
        self.recent_messages.append(message)
        if len(self.recent_messages) > 10:
            self.recent_messages.pop(0)
        if entities:
            self.recent_entities.append(entities)
            if len(self.recent_entities) > 10:
                self.recent_entities.pop(0)
            last = list(self.recent_entities[-3:])
            product_count = sum(1 for e in last if e.get("product_type"))
            self.repeated_intent = product_count

    def merge_entities(self, entities: dict) -> dict:
        merged = dict(entities)
        if not merged.get("product_type") and self.last_product_type:
            merged["product_type"] = self.last_product_type
        if not merged.get("color") and self.last_color:
            merged["color"] = self.last_color
        if not merged.get("size") and self.last_size:
            merged["size"] = self.last_size
        if not merged.get("gender") and self.last_gender:
            merged["gender"] = self.last_gender
        if not merged.get("style") and self.last_style:
            merged["style"] = self.last_style
        if not merged.get("occasion") and self.last_occasion:
            merged["occasion"] = self.last_occasion
        return merged

    def persist_entities(self, entities: dict) -> None:
        if entities.get("product_type"):
            self.last_product_type = entities["product_type"]
        if entities.get("color"):
            self.last_color = entities["color"]
        if entities.get("size"):
            self.last_size = entities["size"]
        if entities.get("gender"):
            self.last_gender = entities["gender"]
        if entities.get("style"):
            self.last_style = entities["style"]
        if entities.get("occasion"):
            self.last_occasion = entities["occasion"]

    def has_product_history(self) -> bool:
        return bool(self.last_product_type or self.last_product_name)

    def get_context_summary(self) -> str:
        parts = []
        if self.last_gender:
            parts.append(f"género: {self.last_gender}")
        if self.last_product_type:
            parts.append(f"producto: {self.last_product_type}")
        if self.last_color:
            parts.append(f"color: {self.last_color}")
        if self.last_size:
            parts.append(f"talla: {self.last_size}")
        if self.last_style:
            parts.append(f"estilo: {self.last_style}")
        if self.last_occasion:
            parts.append(f"ocasión: {self.last_occasion}")
        return " | ".join(parts) if parts else "sin contexto"


class ConversationMemoryManager:
    def __init__(self) -> None:
        self._stores: dict[str, ConversationContext] = {}

    def get_or_create(self, conversation_id: UUID | str) -> ConversationContext:
        key = str(conversation_id)
        if key not in self._stores:
            self._stores[key] = ConversationContext()
            logger.debug("Created memory for conversation %s", key)
        return self._stores[key]

    def clear(self, conversation_id: UUID | str) -> None:
        key = str(conversation_id)
        self._stores.pop(key, None)

    def size(self) -> int:
        return len(self._stores)
