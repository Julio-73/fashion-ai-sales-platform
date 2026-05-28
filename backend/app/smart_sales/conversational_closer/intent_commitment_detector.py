from dataclasses import dataclass, field
from enum import Enum


class CommitmentLevel(str, Enum):
    browsing = "browsing"
    interested = "interested"
    committed = "committed"
    ready_to_buy = "ready_to_buy"


@dataclass
class CommitmentResult:
    level: CommitmentLevel = CommitmentLevel.browsing
    confidence: float = 0.0
    detected_product: str = ""
    detected_size: str = ""
    detected_color: str = ""
    triggers: list[str] = field(default_factory=list)


BROWSING_PATTERNS: list[tuple[str, float]] = [
    (r"\b(?:qué tienes|qué hay|muéstrame|enséñame|ver)\b", 0.6),
    (r"\b(?:catálogo|productos|modelos|ropa)\b", 0.5),
    (r"\b(?:busco|ando buscando|estoy viendo|estoy mirando)\b", 0.6),
    (r"\b(?:solo viendo|solo mirando|nada más ver)\b", 0.7),
]

INTERESTED_PATTERNS: list[tuple[str, float]] = [
    (r"\b(?:me gusta|me interesa|se ve bien|se ve bueno)\b", 0.7),
    (r"\b(?:cuéntame|dime más|cómo es|cómo se ve)\b", 0.6),
    (r"\b(?:buena opción|buen modelo|me convence)\b", 0.7),
]

COMMITTED_PATTERNS: list[tuple[str, float]] = [
    (r"\b(?:quiero eso|quiero ese|quiero esa|lo quiero|la quiero)\b", 0.8),
    (r"\b(?:me gusta mucho|me encanta|me fascina)\b", 0.7),
    (r"\b(?:ese modelo|esa pieza|esa prenda)\b", 0.6),
    (r"\b(?:talla\s+\w+|color\s+\w+)\s+(?:tienes|hay|manejan)\b", 0.7),
]

READY_PATTERNS: list[tuple[str, float]] = [
    (r"\b(?:me lo llevo|me la llevo|lo compro|la compro)\b", 0.95),
    (r"\b(?:separar|apartar|reservar|ordena)\b", 0.9),
    (r"\b(?:cómo lo pido|cómo lo compro|lo quiero ya)\b", 0.85),
    (r"\b(?:dame ese|dame esa|quiero comprar|deseo comprar)\b", 0.85),
    (r"\b(?:cuánto cuesta|cuánto sale|precio)\b", 0.6),
    (r"\b(?:delivery|envío|cuánto demora)\b", 0.6),
]


class IntentCommitmentDetector:
    def detect(self, message: str, has_product_history: bool = False) -> CommitmentResult:
        import re

        result = CommitmentResult()
        msg_lower = message.lower().strip()

        for patterns, level in [
            (READY_PATTERNS, CommitmentLevel.ready_to_buy),
            (COMMITTED_PATTERNS, CommitmentLevel.committed),
            (INTERESTED_PATTERNS, CommitmentLevel.interested),
            (BROWSING_PATTERNS, CommitmentLevel.browsing),
        ]:
            for pattern, conf in patterns:
                match = re.search(pattern, msg_lower)
                if match:
                    result.level = level
                    result.confidence = conf
                    result.triggers.append(match.group())
                    break
            if result.triggers:
                break

        if not result.triggers:
            if has_product_history:
                result.level = CommitmentLevel.interested
                result.confidence = 0.4
            else:
                result.level = CommitmentLevel.browsing
                result.confidence = 0.0

        # detect size
        size_m = re.search(r"talla\s+(\w+)", msg_lower)
        if size_m:
            result.detected_size = size_m.group(1)

        color_m = re.search(r"color\s+(\w+)", msg_lower)
        if color_m:
            result.detected_color = color_m.group(1)

        prod_m = re.search(r"(?:el|la|ese|esa)\s+(\w+(?:\s+\w+){0,3})", msg_lower)
        if prod_m and not any(kw in msg_lower for kw in ["qué", "cuál", "tienes"]):
            result.detected_product = prod_m.group(1)

        return result

    def should_attempt_close(self, result: CommitmentResult) -> bool:
        return result.level in (CommitmentLevel.committed, CommitmentLevel.ready_to_buy)

    def should_recommend(self, result: CommitmentResult) -> bool:
        return result.level in (CommitmentLevel.browsing, CommitmentLevel.interested)
