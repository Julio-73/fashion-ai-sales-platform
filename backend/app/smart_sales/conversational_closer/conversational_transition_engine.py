import random

TRANSITION_PAIRS: list[tuple[str, str, str]] = [
    # (trigger_word, transition, suggestion)
    ("gracias", "Por cierto,", "esa prenda combina demasiado bien con unos jeans negros slim fit."),
    ("gracias", "Ya que estamos,", "ese estilo queda brutal con zapatillas blancas."),
    ("gracias", "A propósito,", "si te gusta ese look, también tengo accesorios que le van perfecto."),
    ("ok", "Y algo más,", "ese modelo también está disponible en otros colores."),
    ("ok", "Además,", "si quieres armar un outfit completo, puedo recomendarte más piezas."),
    ("perfecto", "Por cierto,", "esa prenda es súper versátil, la puedes usar de varias formas."),
    ("me gusta", "Ya que te gusta ese estilo,", "también tengo opciones similares que te pueden interesar."),
    ("me gusta", "Si te va ese vibe,", "déjame mostrarte algo más que combina perfecto."),
    ("talla", "Perfecto,", "y si quieres también te recomiendo cómo combinarlo."),
    ("cuánto", "Hablando de precios,", "ese modelo tiene una calidad-precio increíble."),
]

CATEGORY_TRANSITIONS: dict[str, list[str]] = {
    "polo": [
        "Ese polo queda brutal con joggers negros.",
        "Combínalo con jeans de corte recto para un look casual.",
    ],
    "camisa": [
        "Esa camisa se ve genial con un blazer oscuro.",
        "Combínala con pantalón de vestir para look formal.",
    ],
    "casaca": [
        "Esa casaca combina perfecto con jeans negros.",
        "Úsala con zapatillas blancas para un look urbano.",
    ],
    "pantalon": [
        "Esos pantalones se ven geniales con zapatillas blancas.",
        "Combínalos con una camiseta básica para look diario.",
    ],
    "zapatilla": [
        "Esas zapatillas quedan con casi todo.",
        "Combínalas con joggers o jeans para look urbano.",
    ],
}


class ConversationalTransitionEngine:
    def get_transition(self, message: str, product_category: str = "") -> str:
        msg_lower = message.lower().strip()

        for trigger, transition, suggestion in TRANSITION_PAIRS:
            if trigger in msg_lower:
                return f"{transition} {suggestion}"

        if product_category:
            suggestions = CATEGORY_TRANSITIONS.get(product_category.lower(), [])
            if suggestions:
                return f"Por cierto, {random.choice(suggestions)}"

        return ""

    def build_natural_segue(self, current_topic: str, next_topic: str) -> str:
        segues = [
            f"Y hablando de {next_topic},",
            f"Ya que mencionas {current_topic}, también tengo opciones de {next_topic}.",
            f"Si te gusta {current_topic}, te va a encantar lo que tengo en {next_topic}.",
        ]
        return random.choice(segues)
