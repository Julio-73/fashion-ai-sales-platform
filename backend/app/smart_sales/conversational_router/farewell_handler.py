FAREWELL_RESPONSES: list[str] = [
    "Perfecto 😊 Gracias por visitarnos. Que tengas un excelente día.",
    "¡Listo! 😊 Fue un gusto atenderte. Que estés muy bien.",
    "Perfecto entonces 😊 Gracias por tu tiempo. Cualquier cosa, acá estoy.",
    "Con gusto 😊 Que tengas un lindo día. Cuando necesites algo más, ya sabes.",
    "¡Encantado de ayudarte! 🙌 Que te vaya súper bien.",
    "Perfecto 😊 Me alegra haber podido ayudarte. Hasta luego.",
    "Gracias a ti por confiar 🙌 Que estés muy bien. Cualquier cosa, me dices.",
    "Todo listo entonces 😊 Que tengas un excelente resto del día.",
    "Fue un placer asistirte 🔥 Que te vaya excelente.",
    "¡Listo, todo resuelto! 😊 Cuídate mucho y hasta pronto.",
]

_context_index: dict[str, int] = {}


def get_farewell_response(conversation_id: str | None = None) -> str:
    key = conversation_id or "__global__"
    idx = _context_index.get(key, 0) % len(FAREWELL_RESPONSES)
    _context_index[key] = idx + 1
    return FAREWELL_RESPONSES[idx]
