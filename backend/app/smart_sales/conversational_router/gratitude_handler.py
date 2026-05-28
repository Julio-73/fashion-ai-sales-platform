import random


GRATITUDE_RESPONSES: list[str] = [
    "Con gusto 😊 Si luego quieres combinar esa casaca con zapatillas o jeans, puedo ayudarte.",
    "Encantado 🔥 Y si deseas armar el outfit completo, aquí estoy.",
    "Perfecto 👌 Cualquier cosa, te ayudo a encontrar más opciones.",
    "A ti por confiar 🙌 Si necesitas algo más, acá me tienes.",
    "Un placer 😊 Recuerda que puedo ayudarte a combinar o elegir accesorios.",
    "De nada 🔥 Si quieres te enseño cómo queda ese modelo con otras prendas.",
    "¡Gracias a ti! 😎 Siempre que quieras ver más novedades, avísame.",
    "Contento de ayudar 😊 Si quieres luego te recomiendo outfits completos.",
    "Fue un gusto 🔥 Y si algún día quieres cambiar de estilo, aquí estoy.",
    "¡Listo! 😊 Ya sabes, para lo que necesites estoy acá.",
]

_closing_offers: list[str] = [
    " ¿Quieres que te ayude con el pedido?",
    " ¿Te paso más info de esa prenda?",
    "",
    "",
    " ¿Necesitas saber tallas o colores disponibles?",
]

_context_index: dict[str, int] = {}


def get_gratitude_response(conversation_id: str | None = None) -> str:
    key = conversation_id or "__global__"
    idx = _context_index.get(key, 0) % len(GRATITUDE_RESPONSES)
    _context_index[key] = idx + 1
    base = GRATITUDE_RESPONSES[idx]
    offer = random.choice(_closing_offers)
    return base + offer
