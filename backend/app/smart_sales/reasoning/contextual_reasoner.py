import logging
from dataclasses import dataclass

logger = logging.getLogger("ai_sales_agent.smart_sales.reasoning.contextual")


CONTEXT_INFERENCE_MAP: dict[str, list[dict]] = {
    "elegante": [
        {"product_type": "vestido", "style": "elegante", "score": 30},
        {"product_type": "casaca", "style": "elegante", "score": 20},
        {"product_type": "pantalon", "style": "elegante", "score": 15},
        {"product_type": "camisa", "style": "elegante", "score": 15},
        {"product_type": "zapatos", "style": "elegante", "score": 10},
    ],
    "fiesta": [
        {"product_type": "vestido", "style": "elegante", "occasion": "fiesta", "score": 35},
        {"product_type": "zapatos", "style": "elegante", "occasion": "fiesta", "score": 15},
        {"product_type": "accesorio", "occasion": "fiesta", "score": 10},
    ],
    "casual": [
        {"product_type": "polo", "style": "casual", "score": 25},
        {"product_type": "pantalon", "style": "casual", "score": 20},
        {"product_type": "chompa", "style": "casual", "score": 20},
        {"product_type": "zapatillas", "style": "casual", "score": 15},
        {"product_type": "short", "style": "casual", "score": 10},
    ],
    "urbano": [
        {"product_type": "chompa", "style": "oversize", "score": 25},
        {"product_type": "pantalon", "style": "casual", "score": 20},
        {"product_type": "zapatillas", "style": "deportivo", "score": 20},
        {"product_type": "polo", "style": "oversize", "score": 15},
        {"product_type": "gorro", "score": 10},
    ],
    "deportivo": [
        {"product_type": "zapatillas", "style": "deportivo", "score": 30},
        {"product_type": "short", "style": "deportivo", "score": 20},
        {"product_type": "polo", "style": "deportivo", "score": 15},
        {"product_type": "pantalon", "style": "deportivo", "score": 15},
    ],
    "trabajo": [
        {"product_type": "camisa", "style": "elegante", "score": 25},
        {"product_type": "pantalon", "style": "elegante", "score": 25},
        {"product_type": "zapatos", "style": "elegante", "score": 15},
        {"product_type": "casaca", "style": "elegante", "score": 15},
        {"product_type": "accesorio", "score": 5},
    ],
    "invierno": [
        {"product_type": "casaca", "style": "casual", "score": 25},
        {"product_type": "chompa", "style": "casual", "score": 25},
        {"product_type": "pantalon", "style": "casual", "score": 15},
        {"product_type": "gorro", "score": 10},
        {"product_type": "bufanda", "score": 10},
    ],
    "playa": [
        {"product_type": "short", "style": "casual", "score": 25},
        {"product_type": "polo", "style": "casual", "score": 20},
        {"product_type": "bikini", "score": 20},
        {"product_type": "zapatillas", "style": "casual", "score": 15},
        {"product_type": "gorro", "score": 10},
    ],
    "streetwear": [
        {"product_type": "chompa", "style": "oversize", "score": 25},
        {"product_type": "pantalon", "style": "oversize", "score": 20},
        {"product_type": "zapatillas", "style": "casual", "score": 20},
        {"product_type": "polo", "style": "oversize", "score": 15},
        {"product_type": "gorro", "style": "casual", "score": 10},
    ],
}


@dataclass
class InferredIntent:
    product_type: str | None = None
    color: str | None = None
    size: str | None = None
    gender: str | None = None
    style: str | None = None
    occasion: str | None = None
    confidence: float = 0.0
    inference_reason: str = ""


class ContextualReasoner:
    def infer_context(self, user_message: str, inferred: dict) -> dict:
        enhanced = dict(inferred)
        message_lower = user_message.lower()

        style_keywords = {
            "elegante": ["elegante", "formal", "fino", "chic", "vestir", "cocktail", "gala", "fiesta"],
            "casual": ["casual", "diario", "comodo", "informal", "relajado"],
            "urbano": ["urbano", "urban", "ciudad", "callejero", "street"],
            "deportivo": ["deportivo", "sport", "running", "gym", "deporte"],
            "streetwear": ["streetwear", "hip hop", "rap", "skate", "trap"],
            "oversize": ["oversize", "holgado", "suelto", "ancho"],
        }

        detected_styles = []
        for style, kws in style_keywords.items():
            if any(kw in message_lower for kw in kws):
                detected_styles.append(style)

        if not enhanced.get("style") and detected_styles:
            enhanced["style"] = detected_styles[0]

        if not enhanced.get("product_type") or not enhanced.get("style"):
            for kw, inferences in CONTEXT_INFERENCE_MAP.items():
                if kw in message_lower or any(kw in message_lower for kw in self._expansion(kw)):
                    if inferences:
                        if not enhanced.get("style"):
                            enhanced["style"] = inferences[0].get("style")
                        if not enhanced.get("product_type"):
                            enhanced["product_type"] = inferences[0].get("product_type")
                        enhanced["confidence"] = max(enhanced.get("confidence", 0), 0.6)
                        break

        return enhanced

    def infer_from_context(self, msg_entities: dict, memory_entities: dict) -> dict:
        merged = dict(memory_entities)
        for key in ("product_type", "color", "size", "gender", "style", "occasion"):
            if msg_entities.get(key):
                merged[key] = msg_entities[key]
            elif key not in merged:
                merged[key] = None
        return merged

    def generate_follow_up_questions(self, entities: dict, confidence: float) -> list[str]:
        questions = []
        if entities.get("product_type") and not entities.get("style") and not entities.get("occasion"):
            if entities["product_type"] in ("vestido", "vestidos"):
                questions.extend(["¿Buscas algo largo o corto?", "¿Elegante o casual?"])
            elif entities["product_type"] in ("zapatillas",):
                questions.extend(["¿Urbanas, deportivas o casuales?"])
            elif entities["product_type"] in ("chompa", "casaca", "chompas", "casacas"):
                questions.extend(["¿Prefieres oversize o slim fit?"])
            elif entities["product_type"] in ("pantalon", "jean"):
                questions.extend(["¿Recto, slim fit o jogger?"])
            elif entities["product_type"] in ("polo", "camisa"):
                questions.extend(["¿Prefieres manga larga o corta?"])
            else:
                questions.append("¿Buscas algo en particular?")

        if entities.get("color") and not entities.get("product_type"):
            questions.append("¿Buscas polos, casacas, jeans o zapatillas en ese color?")

        if entities.get("occasion") and not entities.get("product_type") and not entities.get("style"):
            occasion_qs = {
                "fiesta": "¿Prefieres un vestido elegante, traje o algo más casual?",
                "trabajo": "¿Ropa formal o casual elegante?",
                "deporte": "¿Zapatillas, shorts o polos deportivos?",
                "playa": "¿Bikini, short o polos ligeros?",
            }
            q = occasion_qs.get(entities["occasion"], "¿Qué tipo de prenda buscas?")
            questions.append(q)

        return questions[:2]

    def _expansion(self, kw: str) -> list[str]:
        expansions = {
            "elegante": ["formal", "chic", "vestir", "cocktail"],
            "fiesta": ["evento", "boda", "discoteca", "noche", "gala"],
            "casual": ["diario", "comodo", "informal", "relajado", "todos los días"],
            "urbano": ["urban", "ciudad", "callejero"],
            "deportivo": ["sport", "gym", "deporte", "running"],
            "invierno": ["frio", "abrigo", "otoño"],
            "playa": ["verano", "tropical", "balneario"],
            "streetwear": ["oversize", "hip hop"],
        }
        return expansions.get(kw, [])
