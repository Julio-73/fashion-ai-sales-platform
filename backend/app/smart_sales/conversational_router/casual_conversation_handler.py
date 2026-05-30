CASUAL_RESPONSES: list[str] = [
    "¡Muy bien, gracias por preguntar! 😊 Estoy aquí para ayudarte a encontrar lo que buscas.",
    "¡Todo bien por acá! 🔥 ¿Y tú qué tal? ¿En qué puedo ayudarte?",
    "Genial 😊 ¿Qué más te gusta? Cuéntame y vemos qué tenemos.",
    "Perfecto 🔥 Si quieres te muestro más estilos similares.",
    "Dale 👌 ¿Buscas algo más o con eso estamos?",
    "¡Me alegra! 😎 Si se te ocurre algo más, aquí estoy.",
    "Excelente 🙌 Ya sabes que para cualquier cosa, acá me tienes.",
    "Qué bien 😊 ¿Quieres que te recomiende algo más o ya estás bien?",
    "Fino 🔥 ¿Necesitas ayuda con algo más?",
    "Cool 😎 Por si acaso, si quieres armar outfit completo, puedo ayudarte.",
    "Listo 🙌 Si luego quieres ver más novedades, avísame.",
    "Bacán 😊 Recuerda que tengo más estilos si quieres variar.",
    "¡Muy bien! 😊 Siempre es un gusto conversar. ¿En qué más puedo ayudarte?",
    "¡Contento de que estés por aquí! 🔥 ¿Buscas algo en especial?",
]

_status_questions: list[str] = [
    "¿cómo estás",
    "cómo te va",
    "cómo andas",
    "todo bien",
    "qué tal tu día",
    "cómo te sientes",
    "cómo está todo",
]


def _is_status_question(message: str) -> bool:
    msg = message.lower().strip()
    for q in _status_questions:
        if msg.startswith(q) or msg == q:
            return True
    return False


_context_index: dict[str, int] = {}


def get_casual_response(conversation_id: str | None = None, user_message: str | None = None) -> str:
    key = conversation_id or "__global__"
    if user_message and _is_status_question(user_message):
        return CASUAL_RESPONSES[0]
    idx = _context_index.get(key, 0) % len(CASUAL_RESPONSES)
    _context_index[key] = idx + 1
    return CASUAL_RESPONSES[idx]
