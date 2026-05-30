import random


GRATITUDE_RESPONSES: list[str] = [
    "Con gusto 😊 Si más adelante necesitas ayuda para elegir otra prenda, aquí estaré.",
    "Un placer 😊 Cuando quieras, acá estaré para ayudarte.",
    "A ti por tu confianza 🙌 Que tengas un excelente día.",
    "De nada 😊 Estoy aquí para cuando me necesites.",
    "Encantado de ayudar 🔥 Si luego surge algo, no dudes en escribirme.",
    "¡Gracias a ti! 😎 Espero verte pronto de vuelta.",
    "Fue un gusto asistirte 😊 Para cualquier cosa, acá me tienes.",
    "Contento de haber podido ayudar 🙌 Que estés muy bien.",
    "Con gusto, para eso estoy 😊 Cuídate mucho.",
    "¡Listo! 😊 Cuando necesites algo más, ya sabes dónde encontrarme.",
]

_closing_offers: list[str] = [
    "",
    "",
    "",
    "",
]

_context_index: dict[str, int] = {}


def get_gratitude_response(conversation_id: str | None = None) -> str:
    key = conversation_id or "__global__"
    idx = _context_index.get(key, 0) % len(GRATITUDE_RESPONSES)
    _context_index[key] = idx + 1
    base = GRATITUDE_RESPONSES[idx]
    offer = random.choice(_closing_offers)
    return base + offer
