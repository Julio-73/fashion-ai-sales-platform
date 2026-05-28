import logging
from dataclasses import dataclass, field

logger = logging.getLogger("smart_sales.human_sales.styling")


STYLING_BY_CATEGORY: dict[str, list[str]] = {
    "polo": [
        "Queda brutal con joggers negros.",
        "Combínalo con jeans de corte recto.",
        "Se ve genial con bermudas de lino.",
        "Perfecto con chinos beige.",
        "Ideal con pantalón de vestir slim.",
    ],
    "camisa": [
        "Combínala con un blazer oscuro para un look elegante.",
        "Se ve muy bien con jeans oscuros.",
        "Perfecta con pantalón de vestir.",
        "Ideal con chinos y zapatos de cuero.",
    ],
    "camiseta": [
        "Ideal con jeans oversize.",
        "Combínala con joggers para un look casual.",
        "Se ve genial con bermudas.",
        "Perfecta con chaqueta encima.",
    ],
    "pantalon": [
        "Combínalos con una camiseta básica.",
        "Se ven geniales con zapatillas blancas.",
        "Perfectos con un polo oversize.",
        "Ideal con camisa por fuera.",
    ],
    "vestido": [
        "Combínalo con tacones para evento elegante.",
        "Se ve genial con zapatillas para look casual.",
        "Perfecto con chaqueta de cuero.",
        "Ideal con sandalias en verano.",
    ],
    "zapatilla": [
        "Combínalas con joggers o jeans.",
        "Se ven geniales con shorts.",
        "Perfectas para look urbano.",
        "Ideal con cualquier outfit casual.",
    ],
    "chaqueta": [
        "Combínala con un outfit monocromático.",
        "Se ve genial sobre camiseta básica.",
        "Perfecta para darle estilo a cualquier look.",
        "Ideal con jeans y zapatillas.",
    ],
    "blazer": [
        "Combínalo con camisa blanca y pantalón formal.",
        "Se ve genial con jeans oscuros y zapatos.",
        "Perfecto para evento de noche.",
        "Ideal con vestido o falda elegante.",
    ],
    "jean": [
        "Combínalos con cualquier polo o camiseta.",
        "Se ven geniales con zapatillas blancas.",
        "Perfectos para look diario.",
    ],
}

STYLING_BY_COLOR: dict[str, list[str]] = {
    "negro": [
        "El negro combina con todo.",
        "El negro es súper versátil.",
        "Ideal para un look monocromático.",
    ],
    "blanco": [
        "El blanco da un look fresco y limpio.",
        "Combínalo con colores oscuros para contraste.",
    ],
    "rojo": [
        "El rojo es un color que llama la atención.",
        "Combínalo con negro para un look poderoso.",
    ],
}

STYLING_BY_OCCASION: dict[str, list[str]] = {
    "fiesta": [
        "Para fiesta elegante combínalo con accesorios metálicos.",
        "Perfecto para eventos nocturnos.",
        "Ideal para ocasiones especiales.",
    ],
    "formal": [
        "Para evento formal, combínalo con zapatos de vestir.",
        "Perfecto para reuniones y citas importantes.",
    ],
    "casual": [
        "Para el día a día, combínalo con tus básicos favoritos.",
        "Perfecto para salidas casuales.",
    ],
    "deportivo": [
        "Ideal para look sporty chic.",
        "Combínalo con accesorios deportivos.",
    ],
}


@dataclass
class StylingAdvice:
    advice: str = ""
    category: str = ""
    sources: list[str] = field(default_factory=list)
    should_use: bool = False


class StylingAdvisor:
    def get_styling_advice(
        self,
        category: str | None = None,
        color: str | None = None,
        occasion: str | None = None,
    ) -> StylingAdvice:
        import random

        advice = StylingAdvice()

        candidates: list[str] = []

        if category:
            cat_advice = STYLING_BY_CATEGORY.get(category.lower())
            if cat_advice:
                candidates.extend(cat_advice)
                advice.category = category

        if color:
            color_advice = STYLING_BY_COLOR.get(color.lower())
            if color_advice:
                candidates.extend(color_advice)

        if occasion:
            occ_advice = STYLING_BY_OCCASION.get(occasion.lower())
            if occ_advice:
                candidates.extend(occ_advice)

        if candidates:
            advice.advice = random.choice(candidates)
            advice.should_use = True

        return advice
