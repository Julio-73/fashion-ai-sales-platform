import logging
from dataclasses import dataclass
from random import choice

from app.smart_sales.contextual_commitment.selected_product_tracker import (
    CommitmentData,
)

logger = logging.getLogger("ai_sales_agent.smart_sales.contextual_commitment.confirmation")

CONFIRMATION_TEMPLATES: list[str] = [
    "Perfecto \U0001F44C\n{product} {color_phrase}{size_phrase}s\u00ed est\u00e1 disponible.",
    "S\u00ed claro \U0001F525\n{product} {color_phrase}{size_phrase}est\u00e1 saliendo much\u00edsimo esta semana.",
    "Buena elecci\u00f3n \U0001F60A\n{product} {color_phrase}{size_phrase}es un modelo espectacular.",
    "\u00a1Excelente! \u2728\n{product} {color_phrase}{size_phrase}es una prenda premium que no pasa desapercibida.",
]

AVAILABILITY_LINES: list[str] = [
    "Lo tenemos en stock y listo para env\u00edo inmediato.",
    "Tenemos varias unidades disponibles.",
    "Est\u00e1 disponible y con entrega en 24-48 horas.",
    "S\u00ed, est\u00e1 en stock y con buena disponibilidad.",
]

SIZE_CONFIRMATION: list[str] = [
    "La talla {size} est\u00e1 disponible \u2705",
    "En talla {size} tenemos stock \u2705",
    "Talla {size} disponible sin problema \U0001F44D",
]

COLOR_CONFIRMATION: list[str] = [
    "El color {color} es uno de los m\u00e1s vendidos.",
    "En {color} se ve incre\u00edble.",
    "El {color} combina con todo.",
]


@dataclass
class ConfirmationResponse:
    text: str
    source: str = "confirmation"


class EliteProductConfirmation:
    def generate(
        self,
        commitment: CommitmentData,
        user_message: str,
        price_range: str | None = None,
    ) -> ConfirmationResponse | None:
        if not commitment or not commitment.is_committed():
            return None

        product = commitment.selected_product
        if not product:
            return None

        color_phrase = ""
        if commitment.selected_color:
            color_line = choice(COLOR_CONFIRMATION).format(color=commitment.selected_color)
            color_phrase = f"en {commitment.selected_color} — {color_line}\n"

        size_phrase = ""
        if commitment.selected_size:
            size_line = choice(SIZE_CONFIRMATION).format(size=commitment.selected_size)
            size_phrase = f"{size_line}\n"

        template = choice(CONFIRMATION_TEMPLATES)
        text = template.format(
            product=product,
            color_phrase=f"en {commitment.selected_color} " if commitment.selected_color else "",
            size_phrase=f"talla {commitment.selected_size} " if commitment.selected_size else "",
        )

        if price_range:
            text += f"\n{price_range}"

        availability = choice(AVAILABILITY_LINES)
        text += f"\n{availability}"

        if commitment.confirmation_count >= 2:
            text += (
                "\n\n\u00bfTe ayudo con el proceso de compra? "
                "Puedo indicarte los pasos para que lo recibas en casa \U0001F7E2"
            )

        logger.info(
            "Generated confirmation for product '%s' (conv level=%s)",
            product, commitment.commitment_level,
        )
        return ConfirmationResponse(text=text, source="confirmation")
