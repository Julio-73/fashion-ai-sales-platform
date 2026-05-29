import logging
from dataclasses import dataclass, field
from random import choice

from app.smart_sales.contextual_commitment.selected_product_tracker import (
    CommitmentData,
)

logger = logging.getLogger("ai_sales_agent.smart_sales.contextual_commitment.recovery")


RECOVERY_TEMPLATES: list[str] = [
    "Entiendo perfectamente \U0001F60A\nTenemos otras opciones que podr\u00edan gustarte.",
    "No hay problema \U0001F44C\nD\u00e9jame mostrarte alternativas que se ajusten mejor a lo que buscas.",
    "\u00a1Claro! \U0001F60A\nAqu\u00ed te van otras opciones que podr\u00edan interesarte.",
    "Por supuesto \u2728\nTenemos varios modelos similares que te van a encantar.",
]

RECATEGORY_TEMPLATES: list[str] = [
    "Dentro de {category}, tenemos estas alternativas:",
    "En {category} tambi\u00e9n tenemos opciones muy interesantes:",
    "Siguiendo con {category}, mira estas opciones:",
]


@dataclass
class RecoveryResult:
    needs_recovery: bool = False
    recovered_category: str | None = None
    recovery_prompt: str | None = None
    rejected_products: list[str] = field(default_factory=list)


class RejectionRecoveryEngine:
    def process(
        self,
        commitment: CommitmentData,
        user_message: str,
    ) -> RecoveryResult:
        result = RecoveryResult()

        has_rejection = commitment.last_rejection_category is not None
        if not has_rejection:
            return result

        result.needs_recovery = True
        result.rejected_products = list(commitment.rejected_products)

        if commitment.last_rejection_category:
            result.recovered_category = commitment.last_rejection_category
            template = choice(RECATEGORY_TEMPLATES)
            result.recovery_prompt = template.format(
                category=commitment.last_rejection_category,
            )
        else:
            result.recovery_prompt = choice(RECOVERY_TEMPLATES)

        logger.info(
            "Recovery needed for category=%s, rejected=%s",
            result.recovered_category,
            result.rejected_products,
        )
        return result

    def build_recovery_context(
        self,
        recovery: RecoveryResult,
        current_entities: dict,
    ) -> dict:
        updated = dict(current_entities)
        if recovery.recovered_category:
            updated["product_type"] = recovery.recovered_category
        return updated
