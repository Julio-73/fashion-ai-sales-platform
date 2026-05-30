import logging
import re
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("ai_sales_agent.smart_sales.contextual_commitment.tracker")


class CommitmentLevel(Enum):
    none = 0
    browsing = 1
    interested = 2
    selected = 3
    confirmed = 4


PRODUCT_CONFIRMATION_PATTERNS: list[re.Pattern] = [
    re.compile(r'\b(quiero\s+es[eo]|quiero\s+este|quiero\s+esa|quiero\s+ese)\b', re.IGNORECASE),
    re.compile(r'\b(me\s+(gusta|llevo|quedo)\s+(es[eo]|este|esta|esa|ese))\b', re.IGNORECASE),
    re.compile(r'\b(me\s+(gusta|llevo|quedo)\s+(el|la|lo)\s+\w+)\b', re.IGNORECASE),
    re.compile(r'\b(quiero\s+(el|la|lo)\s+\w+)\b', re.IGNORECASE),
    re.compile(r'\b(ese?\s+(azul|negro|rojo|blanco|gris|verde|rosa))\b', re.IGNORECASE),
    re.compile(r'\b((el|la)\s+(modelo|producto|polo|vestido|casaca|jean|chompa|short|camisa|zapatilla|blazer|hoodie)\s+\w+)\b', re.IGNORECASE),
    re.compile(r'\b(ese\s+(modelo|color|talla|estilo))\b', re.IGNORECASE),
    re.compile(r'\b(dame\s+(el\s+)?(es[eo]|este|esta|esa|ese))\b', re.IGNORECASE),
    re.compile(r'\b(lo\s+quiero)\b', re.IGNORECASE),
    re.compile(r'\b(compro|compra(r)?|lo\s+compro|me\s+lo\s+llevo)\b', re.IGNORECASE),
    re.compile(r'\b(me\s+encanta\s+(el|la|lo)\s+\w+)\b', re.IGNORECASE),
    re.compile(r'\bel\s+(premium|black|white|classic|pro|max|elite|street|urban|sport|slim|fit|cargo|denim|leather|casual|formal|night|sunset|winter|summer|classic|essential)\s+\w+\b', re.IGNORECASE),
]

SIZE_PATTERNS: list[re.Pattern] = [
    re.compile(r'\b(talla\s+([xlsmxl]+))\b', re.IGNORECASE),
    re.compile(r'\b([xlsmxl]+)\s*$', re.IGNORECASE),
    re.compile(r'\b(talle\s+([xlsmxl]+))\b', re.IGNORECASE),
]

COLOR_REFERENCE_PATTERNS: list[re.Pattern] = [
    re.compile(r'\b(en\s+(azul|negro|rojo|blanco|gris|beige|verde|rosa|amarillo|naranja|morado|marron))\b', re.IGNORECASE),
    re.compile(r'\b(color\s+(azul|negro|rojo|blanco|gris|beige|verde|rosa|amarillo|naranja|morado|marron))\b', re.IGNORECASE),
]

REJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(r'\bno\s+(me\s+)?(gusta|convence|interesa|quiero)\b', re.IGNORECASE),
    re.compile(r'\b(muy\s+(caro|cara|costoso|grande|pequen[oa]|chico[oa]))\b', re.IGNORECASE),
    re.compile(r'\b(otr[oa]\s+(modelo|opcion|producto|color|talla|estilo))\b', re.IGNORECASE),
    re.compile(r'\b(no\s+(gracias|thanks))\b', re.IGNORECASE),
    re.compile(r'\bbusco\s+otr[oa]\b', re.IGNORECASE),
]


@dataclass
class CommitmentData:
    selected_product: str | None = None
    selected_product_id: str | None = None
    selected_color: str | None = None
    selected_size: str | None = None
    selected_category: str | None = None
    commitment_level: CommitmentLevel = CommitmentLevel.none
    reservation_confirmed: bool = False
    last_rejection_category: str | None = None
    rejected_products: set[str] = field(default_factory=set)
    confirmation_count: int = 0

    def is_committed(self) -> bool:
        return self.commitment_level.value >= CommitmentLevel.selected.value

    def is_confirmed(self) -> bool:
        return self.commitment_level.value >= CommitmentLevel.confirmed.value

    def reset_selection(self) -> None:
        self.selected_product = None
        self.selected_product_id = None
        self.selected_color = None
        self.selected_size = None
        self.commitment_level = CommitmentLevel.none
        self.reservation_confirmed = False
        self.confirmation_count = 0

    def has_any_selection(self) -> bool:
        return bool(self.selected_product or self.selected_color or self.selected_size)


class SelectedProductTracker:
    def __init__(self) -> None:
        self._stores: dict[str, CommitmentData] = {}

    def get_or_create(self, conversation_id: str) -> CommitmentData:
        if conversation_id not in self._stores:
            self._stores[conversation_id] = CommitmentData()
        return self._stores[conversation_id]

    def detect(self, conversation_id: str, user_message: str) -> CommitmentData:
        data = self.get_or_create(conversation_id)
        message_lower = user_message.lower()

        is_rejection = any(p.search(message_lower) for p in REJECTION_PATTERNS)
        if is_rejection and data.is_committed():
            if data.selected_category:
                data.last_rejection_category = data.selected_category
            if data.selected_product:
                data.rejected_products.add(data.selected_product)
            data.reset_selection()
            data.commitment_level = CommitmentLevel.interested
            logger.info("Rejection detected for conv %s: %s", conversation_id, user_message)
            return data

        is_confirmation = any(p.search(message_lower) for p in PRODUCT_CONFIRMATION_PATTERNS)
        if is_confirmation:
            if data.selected_product:
                data.confirmation_count += 1
                if data.commitment_level.value < CommitmentLevel.confirmed.value:
                    data.commitment_level = CommitmentLevel.confirmed
                return data
            data.commitment_level = CommitmentLevel.selected

        size_match = None
        for p in SIZE_PATTERNS:
            m = p.search(message_lower)
            if m:
                raw = m.group(2) if p.groups > 1 else m.group(1)
                size_match = raw.upper().replace("TALLA", "").replace("TALLE", "").strip()
                break
        if size_match:
            data.selected_size = size_match
            data.commitment_level = CommitmentLevel.confirmed
            logger.info("Size detected for conv %s: %s", conversation_id, size_match)
            return data

        color_match = None
        for p in COLOR_REFERENCE_PATTERNS:
            m = p.search(message_lower)
            if m:
                color_match = m.group(1) if p.groups > 1 else m.group(1)
                color_match = color_match.replace("en ", "").replace("color ", "").strip()
                break
        if color_match:
            data.selected_color = color_match.title()
            if data.is_committed():
                data.commitment_level = CommitmentLevel.confirmed
            logger.info("Color reference detected for conv %s: %s", conversation_id, color_match)
            return data

        if is_confirmation:
            data.commitment_level = CommitmentLevel.selected
            logger.info("Product selected detected for conv %s: %s", conversation_id, user_message)

        return data

    def set_selected_product(
        self,
        conversation_id: str,
        product_name: str,
        product_id: str | None = None,
        category: str | None = None,
    ) -> None:
        data = self.get_or_create(conversation_id)
        data.selected_product = product_name
        if product_id:
            data.selected_product_id = product_id
        if category:
            data.selected_category = category
        data.commitment_level = CommitmentLevel.selected
        logger.info(
            "Product set for conv %s: %s (id=%s, cat=%s)",
            conversation_id, product_name, product_id, category,
        )

    def mark_reserved(self, conversation_id: str) -> None:
        data = self.get_or_create(conversation_id)
        data.reservation_confirmed = True
        data.commitment_level = CommitmentLevel.confirmed
        data.confirmation_count += 1
        logger.info("Reservation confirmed for conv %s: %s", conversation_id, data.selected_product)

    def clear(self, conversation_id: str) -> None:
        self._stores.pop(conversation_id, None)
