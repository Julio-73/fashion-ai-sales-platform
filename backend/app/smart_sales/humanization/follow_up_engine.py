import logging

from app.smart_sales.reasoning.confidence_scorer import ConfidenceResult

logger = logging.getLogger("ai_sales_agent.smart_sales.humanization.follow_up")


FOLLOW_UP_QUESTIONS: dict[str, list[str]] = {
    "vestido": ["¿Buscas algo largo, midi o corto?", "¿Elegante, casual o bohemio?", "¿Para fiesta o uso diario?"],
    "pantalon": ["¿Recto, slim fit, jogger o palazzo?", "¿Casual o formal?", "¿Tela denim, dril o lino?"],
    "jean": ["¿Slim fit, recto o jogger?", "¿Clásico azul, negro o lavado?", "¿Cintura alta o media?"],
    "chompa": ["¿Oversize o ajustada?", "¿Con capucha o sin capucha?", "¿Algodón o polar?"],
    "casaca": ["¿Oversize o slim fit?", "¿Impermeable o ligera?", "¿Con capucha?"],
    "polo": ["¿Manga larga o corta?", "¿Clásico o moderno?", "¿Color liso o estampado?"],
    "camisa": ["¿Manga larga o corta?", "¿Formal o casual?", "¿Lisa o con estampado?"],
    "zapatillas": ["¿Urbanas, deportivas o casuales?", "¿Para uso diario o entrenar?"],
    "short": ["¿Corto clásico o bermuda?", "¿Deportivo o casual?"],
    "falda": ["¿Larga, midi o corta?", "¿Elegante o casual?"],
    "bikini": ["¿Enterizo o dos piezas?", "¿Deportivo o clásico?"],
}

CATEGORY_FOLLOW_UPS: dict[str, list[str]] = {
    "fiesta": ["¿Prefieres vestido elegante o traje?", "¿Algo clásico o moderno?"],
    "trabajo": ["¿Formal o smart casual?", "¿Traje completo o prendas sueltas?"],
    "deporte": ["¿Para gym, running o yoga?", "¿Prefieres marcas técnicas o casual deportivo?"],
    "playa": ["¿Bikini, short o polos ligeros?", "¿Algo para toda la familia?"],
}

CLARIFICATION_QUESTIONS = [
    "¿Buscas polos, casacas, jeans o zapatillas?",
    "¿Qué tipo de prenda te interesa?",
    "¿Tienes alguna preferencia de estilo?",
]


class FollowUpEngine:
    def generate_questions(self, entities: dict, confidence: ConfidenceResult) -> list[str]:
        if confidence.should_recommend_directly():
            return []
        questions = []
        product_type = entities.get("product_type")
        occasion = entities.get("occasion")

        if not product_type and not occasion:
            return CLARIFICATION_QUESTIONS[:1]

        if product_type:
            if product_type in FOLLOW_UP_QUESTIONS:
                questions.extend(FOLLOW_UP_QUESTIONS[product_type][:2])
            elif product_type == "accesorio":
                questions.append("¿Bolsos, cinturones, gorros o carteras?")

        if occasion and not product_type:
            if occasion in CATEGORY_FOLLOW_UPS:
                questions.append(CATEGORY_FOLLOW_UPS[occasion][0])

        return questions[:2]

    def should_ask_question(self, confidence: ConfidenceResult, follow_up_count: int) -> bool:
        if follow_up_count >= 2:
            return False
        return confidence.should_ask_before_recommend()
