import logging
from dataclasses import dataclass

logger = logging.getLogger("smart_sales.human_sales.closing")


CLOSING_OPENERS: list[str] = [
    "Perfecto.",
    "Buenísima elección.",
    "Excelente, te va a quedar brutal.",
    "Genial, te va a encantar.",
    "Dale, estamos listos.",
]

SIZE_QUESTIONS: list[str] = [
    "¿Cuál es tu talla?",
    "¿Qué talla usas?",
    "¿En qué talla te lo llevas?",
    "¿Tienes preferencia de talla?",
]

COLOR_QUESTIONS: list[str] = [
    "¿Algún color en especial?",
    "¿Tienes preferencia de color?",
    "¿Qué color te gusta más?",
]

CONFIRMATION_TEMPLATES: list[str] = [
    "Te separo el {product_name}.",
    "Te aparto {product_name}.",
    "Dejamos apartado el {product_name}.",
    "Te reservo el {product_name}.",
]

DELIVERY_QUESTIONS: list[str] = [
    "¿Cómo prefieres recibirlo?",
    "¿Lo quieres para delivery o recojo en tienda?",
    "¿Te lo enviamos a casa?",
]

CLOSING_CLOSERS: list[str] = [
    "¿Te parece bien?",
    "¿Listo?",
    "¿Confirmamos?",
    "¿Te ayudo con el pago?",
]

HIGH_INTENT_TRIGGERS: list[str] = [
    "quiero eso", "me gusta", "me lo llevo", "se ve bueno", "lo quiero",
    "me encanta", "perfecto", "dale", "voy por ese", "quiero comprar",
    "lo compro", "la compro", "compro", "lo quiero ya", "lo necesito",
    "talla", "separar", "apartar", "reservar",
]


@dataclass
class ClosingContext:
    should_close: bool = False
    opener: str = ""
    size_question: str = ""
    color_question: str = ""
    confirmation: str = ""
    delivery_question: str = ""
    closer: str = ""
    product_name: str = ""


class ClosingEngine:
    def should_attempt_close(self, message: str) -> bool:
        msg_lower = message.lower().strip()
        for trigger in HIGH_INTENT_TRIGGERS:
            if trigger in msg_lower:
                return True
        return False

    def build_closing(
        self,
        product_name: str = "",
        already_has_size: bool = False,
        already_has_color: bool = False,
    ) -> ClosingContext:
        import random

        ctx = ClosingContext(should_close=True, product_name=product_name)

        ctx.opener = random.choice(CLOSING_OPENERS)
        ctx.confirmation = random.choice(CONFIRMATION_TEMPLATES).format(
            product_name=product_name or "el producto"
        )

        if not already_has_size:
            ctx.size_question = random.choice(SIZE_QUESTIONS)
        if not already_has_color:
            ctx.color_question = random.choice(COLOR_QUESTIONS)

        ctx.delivery_question = random.choice(DELIVERY_QUESTIONS)
        ctx.closer = random.choice(CLOSING_CLOSERS)

        return ctx

    def format_closing_response(self, ctx: ClosingContext) -> str:
        parts = [ctx.opener]

        if ctx.confirmation:
            parts.append(ctx.confirmation)

        if ctx.size_question:
            parts.append(ctx.size_question)

        if ctx.color_question and not ctx.size_question:
            parts.append(ctx.color_question)

        if ctx.delivery_question and ctx.size_question:
            pass

        parts.append(ctx.closer)

        return "\n\n".join(parts)
