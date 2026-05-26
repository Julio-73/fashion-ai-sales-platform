import logging
import re
from dataclasses import dataclass

from app.ai.schemas.ai_schemas import IntentClassification, IntentType

logger = logging.getLogger("ai_sales_agent.ai.classifier")

KEYWORD_RULES: dict[IntentType, list[str]] = {
    IntentType.pricing: [
        "precio", "costar", "cuánto vale", "cuesta", "precios", "valor",
        "price", "cost", "how much", "pricing", "worth",
    ],
    IntentType.purchase_intent: [
        "comprar", "ordenar", "adquirir", "compraría", "quiero comprar",
        "quiero ordenar", "voy a comprar", "me llevo",
        "buy", "purchase", "order", "i want to buy", "would like to get",
    ],
    IntentType.negotiation: [
        "descuento", "regatear", "oferta", "negociar", "más barato", "rebaja",
        "discount", "negotiate", "deal", "cheaper", "best price",
    ],
    IntentType.delivery: [
        "envío", "entrega", "cuándo llega", "domicilio", "mi pedido",
        "shipping", "delivery", "shipped", "arrive", "when will", "tracking",
    ],
    IntentType.greeting: [
        "hola", "buenos días", "buenas tardes", "buenas noches", "saludos",
        "hello", "hi", "good morning", "good afternoon", "hey",
    ],
    IntentType.support: [
        "ayuda", "problema", "error", "ayúdame", "soporte", "asistencia",
        "help", "issue", "problem", "support", "not working",
    ],
    IntentType.return_request: [
        "devolver", "devolución", "reembolso", "cambio", "cancelar orden",
        "quiero devolver", "necesito devolver", "devolver un producto",
        "return", "refund", "send back", "cancel order", "exchange",
    ],
    IntentType.product_question: [
        "color", "material", "disponible", "tiene", "características",
        "de qué", "cómo es", "qué incluye",
        "color", "material", "available", "features", "specs",
    ],
    IntentType.sizing: [
        "talla", "medida", "guía de tallas", "cómo queda", "qué talla",
        "talla me recomiendas", "talla me quedará",
        "sizing", "size chart", "fit", "measurement", "what size",
    ],
}


@dataclass
class ClassifierConfig:
    confidence_threshold: float = 0.15
    keyword_weight: float = 0.3
    length_boost: float = 0.05
    max_length_for_boost: int = 200


class IntentClassifierService:
    def __init__(self, config: ClassifierConfig | None = None) -> None:
        self._config = config or ClassifierConfig()
        self._keyword_map = self._compile_keywords()

    def _compile_keywords(self) -> list[tuple[re.Pattern, IntentType]]:
        compiled: list[tuple[re.Pattern, IntentType]] = []
        for intent, keywords in KEYWORD_RULES.items():
            for kw in keywords:
                pattern = re.compile(re.escape(kw), re.IGNORECASE)
                compiled.append((pattern, intent))
        return compiled

    async def classify(self, message: str) -> IntentClassification:
        message_lower = message.lower().strip()
        if not message_lower:
            return IntentClassification(intent=IntentType.unknown, confidence=0.0)

        scores: dict[IntentType, float] = {}
        matched: dict[IntentType, list[str]] = {}

        for pattern, intent in self._keyword_map:
            match = pattern.search(message_lower)
            if match:
                scores[intent] = scores.get(intent, 0.0) + self._config.keyword_weight
                if intent not in matched:
                    matched[intent] = []
                matched[intent].append(match.group())

        if not scores:
            return IntentClassification(intent=IntentType.unknown, confidence=0.0)

        if len(message_lower) < self._config.max_length_for_boost:
            for intent in scores:
                scores[intent] += self._config.length_boost

        best_intent = max(scores, key=lambda k: scores[k])
        best_score = round(min(scores[best_intent], 1.0), 4)

        if best_score < self._config.confidence_threshold:
            return IntentClassification(intent=IntentType.unknown, confidence=best_score)

        return IntentClassification(
            intent=best_intent,
            confidence=best_score,
            matched_keywords=matched.get(best_intent, []),
        )
