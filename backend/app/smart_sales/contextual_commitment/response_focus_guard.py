import logging
import re
from dataclasses import dataclass

from app.smart_sales.contextual_commitment.selected_product_tracker import CommitmentData

logger = logging.getLogger("ai_sales_agent.smart_sales.contextual_commitment.focus_guard")

CATALOG_LISTING_PATTERNS: list[re.Pattern] = [
    re.compile(r'\b(mira\s+estas\s+opciones)\b', re.IGNORECASE),
    re.compile(r'\b(tenemos\s+estas?\s+(opciones|disponibles|alternativas))\b', re.IGNORECASE),
    re.compile(r'\b(te\s+muestro|te\s+recomiendo)\s+(estas|varias|algunas)\s+opciones\b', re.IGNORECASE),
    re.compile(r'\b(catálogo|catalogo)\b', re.IGNORECASE),
    re.compile(r'\b(m\u00e1s\s+opciones)\b', re.IGNORECASE),
    re.compile(r'\b(lista\s+de\s+productos)\b', re.IGNORECASE),
    re.compile(r'\b(tenemos\s+disponibles)\b', re.IGNORECASE),
    re.compile(r'\b(estos\s+(modelos|productos))\b', re.IGNORECASE),
    re.compile(r'\b(te\s+gustar[ií]a\s+ver)\b', re.IGNORECASE),
    re.compile(r'\b(quieres\s+que\s+te\s+muestre)\b', re.IGNORECASE),
]

MULTIPLE_PRODUCT_PATTERN: re.Pattern = re.compile(
    r'(?:•|\*|-|\d+\.)\s*\w+.*\(?(?:S/|USD|\$)?\s*\d+',
    re.IGNORECASE,
)

# Also block any response that lists 2+ product names with prices/bullets
BULLET_PRODUCT_PATTERN: re.Pattern = re.compile(
    r'(?:•|\*|-)\s+\w+\s+\w+.*(?:S/|USD|\$|precio|soles)',
    re.IGNORECASE,
)


@dataclass
class FocusGuardResult:
    is_blocked: bool = False
    block_reason: str = ""
    contains_catalog_listing: bool = False
    contains_multiple_products: bool = False


class ResponseFocusGuard:
    def check(
        self,
        response: str,
        commitment: CommitmentData | None = None,
    ) -> FocusGuardResult:
        result = FocusGuardResult()

        if not commitment or not commitment.is_committed():
            return result

        for pattern in CATALOG_LISTING_PATTERNS:
            if pattern.search(response):
                result.is_blocked = True
                result.block_reason = "catalog_listing_pattern"
                result.contains_catalog_listing = True
                logger.warning(
                    "Focus guard blocked: catalog listing pattern '%s' in response",
                    pattern.pattern[:40],
                )
                return result

        if MULTIPLE_PRODUCT_PATTERN.search(response):
            result.is_blocked = True
            result.block_reason = "multiple_products_listed"
            result.contains_multiple_products = True
            logger.warning("Focus guard blocked: multiple products listed in response")
            return result

        if BULLET_PRODUCT_PATTERN.search(response):
            result.is_blocked = True
            result.block_reason = "bullet_product_listing"
            result.contains_multiple_products = True
            logger.warning("Focus guard blocked: bullet product listing in response")
            return result

        return result

    def sanitize(self, response: str, commitment: CommitmentData) -> str:
        if not commitment or not commitment.is_committed():
            return response

        for pattern in CATALOG_LISTING_PATTERNS:
            response = pattern.sub("", response)
        response = MULTIPLE_PRODUCT_PATTERN.sub("", response)
        response = BULLET_PRODUCT_PATTERN.sub("", response)
        response = re.sub(r'\n{3,}', '\n\n', response)
        response = response.strip()

        if not response:
            product = commitment.selected_product or "ese producto"
            response = (
                f"Excelente elecci\u00f3n \U0001F44D " 
                f"{product} es una prenda espectacular. "
                f"\u00bfTe ayudo con la talla o prefieres seguir viendo?"
            )

        return response
