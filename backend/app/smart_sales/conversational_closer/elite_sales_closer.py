import random

CLOSING_OPENERS: list[str] = [
    "Excelente elección 🔥",
    "Buenísima decisión 👌",
    "Te va a quedar brutal 😊",
    "Perfecto, es una de las mejores elecciones 🔥",
    "Elegante decisión ✨",
    "Me encanta tu estilo 🔥",
]

PRODUCT_CONFIRMATIONS: list[str] = [
    "Te separo el {product}.",
    "Dejamos apartado {product}.",
    "Reservamos {product} para ti.",
    "{product} está listo para ti.",
]

SIZE_QUESTIONS: list[str] = [
    "¿Cuál es tu talla?",
    "¿Qué talla usas normalmente?",
    "¿En qué talla te lo llevas?",
    "¿Talla S, M o L?",
]

COLOR_QUESTIONS: list[str] = [
    "¿Tienes preferencia de color?",
    "¿Algún color en especial?",
]

STOCK_INFO: list[str] = [
    "Tenemos stock disponible.",
    "Está disponible en varias tallas.",
    "Sí tenemos disponible.",
]

DELIVERY_QUESTIONS: list[str] = [
    "¿Cómo prefieres recibirlo? ¿Delivery o recojo en tienda?",
    "¿Te lo enviamos a casa o pasas a recoger?",
    "¿Lo quieres para delivery?",
]

CLOSING_CLOSERS: list[str] = [
    "¿Te parece bien?",
    "¿Confirmamos?",
    "¿Te ayudo con el pago?",
    "¿Listo?",
]


class EliteSalesCloser:
    def build_closing(
        self,
        product_name: str = "",
        product_category: str = "",
        available_sizes: list[str] | None = None,
        available_colors: list[str] | None = None,
        has_size: bool = False,
        has_color: bool = False,
        total_stock: int = 0,
    ) -> str:
        parts = []

        parts.append(random.choice(CLOSING_OPENERS))

        if product_name:
            confirm = random.choice(PRODUCT_CONFIRMATIONS).format(product=product_name)
            parts.append(confirm)

        if has_size and has_color:
            pass
        elif not has_size and not has_color:
            parts.append(random.choice(SIZE_QUESTIONS))
        elif not has_size:
            parts.append(random.choice(SIZE_QUESTIONS))

        if total_stock > 0 and total_stock <= 5:
            parts.append(f"Eso sí, solo quedan {total_stock} unidades. ¡Aprovecha!")

        if product_name and not has_size:
            if available_sizes:
                sizes_display = ", ".join(available_sizes)
                parts.append(f"Tenemos disponible en {sizes_display}.")
            parts.append(random.choice(SIZE_QUESTIONS))

        parts.append(random.choice(DELIVERY_QUESTIONS))
        parts.append(random.choice(CLOSING_CLOSERS))

        return "\n\n".join(parts)
