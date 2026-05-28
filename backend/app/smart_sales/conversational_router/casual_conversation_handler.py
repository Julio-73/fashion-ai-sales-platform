CASUAL_RESPONSES: list[str] = [
    "Genial 😊 ¿Qué más te gusta?",
    "Perfecto 🔥 Si quieres te muestro más estilos similares.",
    "Dale 👌 ¿Buscas algo más o con eso estamos?",
    "¡Me alegra! 😎 Si se te ocurre algo más, aquí estoy.",
    "Excelente 🙌 Ya sabes que para cualquier cosa, acá me tienes.",
    "Qué bien 😊 ¿Quieres que te recomiende algo más o ya estás bien?",
    "Fino 🔥 ¿Necesitas ayuda con algo más?",
    "Cool 😎 Por si acaso, si quieres armar outfit completo, puedo ayudarte.",
    "Listo 🙌 Si luego quieres ver más novedades, avísame.",
    "Bacán 😊 Recuerda que tengo más estilos si quieres variar.",
]

_context_index: dict[str, int] = {}


def get_casual_response(conversation_id: str | None = None) -> str:
    key = conversation_id or "__global__"
    idx = _context_index.get(key, 0) % len(CASUAL_RESPONSES)
    _context_index[key] = idx + 1
    return CASUAL_RESPONSES[idx]
