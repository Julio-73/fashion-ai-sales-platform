HESITATION_RESPONSES: list[str] = [
    "Claro 😊 tómate tu tiempo. Igual esa prenda está saliendo bastante esta semana 🔥",
    "Sin problema 👌 Cuando quieras te ayudo a comparar modelos.",
    "Entiendo 😊 Igual te recomiendo no esperar mucho porque varias tallas se están agotando.",
    "Por supuesto 🙌 Tómate el tiempo que necesites. Cuando decidas, acá estoy.",
    "Tranqui 😎 Si quieres te guardo la información de ese modelo para que lo veas después.",
    "Dale sin prisa 🔥 Eso sí, te aviso que el stock está volando.",
    "Claro, es una decisión importante 👊 Si quieres te muestro más fotos o detalles.",
    "Entendido 😊 Si luego te interesa ver opciones similares, me dices.",
    "Tómate tu tiempo, obvio 🙌 Y si quieres que te recomiende algo específico, acá estoy.",
    "Sin drama 🔥 Cuando estés listo, me avisas y vemos los detalles.",
]

LOW_PRESSURE: list[str] = [
    " Sin compromiso, obvio 😊",
    " Como tú quieras 👌",
    " Obvio, sin presiones 😎",
]

GENTLE_URGENCY: list[str] = [
    " Aunque igual te recomiendo no perder de vista el modelo.",
    " La tendencia actual se está agotando rápido.",
    " Eso sí, varias tallas ya no son tan fáciles de conseguir.",
]

_context_index: dict[str, int] = {}


def get_hesitation_response(conversation_id: str | None = None) -> str:
    key = conversation_id or "__global__"
    idx = _context_index.get(key, 0) % len(HESITATION_RESPONSES)
    _context_index[key] = idx + 1
    return HESITATION_RESPONSES[idx]
