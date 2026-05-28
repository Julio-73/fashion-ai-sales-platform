GREETINGS: list[str] = [
    "¡Hola! 😊 Bienvenido a Urban Style. ¿Qué tipo de outfit estás buscando hoy?",
    "¡Qué tal! 🔥 ¿Buscas algo urbano, elegante o casual?",
    "Bienvenido 😎 ¿Quieres ver ropa de hombre, mujer o sneakers?",
    "¡Hey! 👋 Bienvenido a Urban Style. ¿Qué estilo te gusta más: streetwear, sport o clásico?",
    "¡Hola! 😊 Qué bueno tenerte por aquí. ¿Hay algo en especial que estés buscando?",
    "¡Qué onda! 🔥 ¿Vienes por ropa casual, algo más formal o sneakers?",
    "Bienvenido! 😎 Cuéntame, ¿qué tipo de look te gustaría armar hoy?",
    "¡Hola! 👊 ¿Buscas outfit completo o algo en particular?",
    "¡Qué tal! 😊 ¿Prefieres estilo urbano, elegante o sport?",
    "Hey! 🔥 ¿Qué se te ofrece hoy? Ropa, zapatillas o accesorios.",
]

GENDER_GREETINGS: dict[str, list[str]] = {
    "hombre": [
        "¡Hola! 😎 ¿Buscas ropa para hombre en especial?",
        "¡Qué tal bro! 🔥 ¿Buscas casacas, polos o sneakers?",
        "Bienvenido 👊 ¿Qué estilo de hombre te gusta: sport, casual o elegante?",
    ],
    "mujer": [
        "¡Hola! 😊 ¿Buscas algo lindo para mujer?",
        "¡Qué tal! 🔥 ¿Vestidos, jeans o casacas?",
        "Bienvenida 😊 ¿Qué look estás buscando hoy?",
        "¡Hola! ✨ ¿Buscas outfit casual, elegante o sport?",
    ],
}

_context_index: dict[str, int] = {}


def get_greeting(conversation_id: str | None = None, gender: str | None = None) -> str:
    key = conversation_id or "__global__"
    if gender and gender.lower() in GENDER_GREETINGS:
        pool = GENDER_GREETINGS[gender.lower()]
    else:
        pool = GREETINGS
    idx = _context_index.get(key, 0) % len(pool)
    _context_index[key] = idx + 1
    return pool[idx]
