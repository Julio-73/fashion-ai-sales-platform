import logging
from dataclasses import dataclass
from uuid import UUID

from app.smart_sales.product_context import ProductContextEngine

logger = logging.getLogger("ai_sales_agent.smart_sales.recommendations")


@dataclass
class Recommendation:
    category: str
    suggestion: str
    products_count: int


UPSELL_MAP: dict[str, list[str]] = {
    "vestido": ["accesorios", "zapatos", "carteras"],
    "pantalon": ["polos", "camisas", "zapatos", "cinturones"],
    "jean": ["polos", "hoodies", "zapatillas", "casacas"],
    "chompa": ["polos", "jeans", "zapatillas", "accesorios"],
    "casaca": ["polos", "jeans", "buzos", "gorros"],
    "polo": ["jeans", "pantalones", "casacas", "zapatillas"],
    "camisa": ["pantalones", "zapatos", "casacas", "corbatas"],
    "short": ["polos", "zapatillas", "gorras", "lentes"],
    "zapatillas": ["medias", "shorts", "polos", "buzos"],
    "falda": ["blusas", "zapatos", "carteras", "cinturones"],
    "bikini": ["lentes", "gorras", "short", "sandalias"],
}

COMPLEMENTARY_UPSELLS: dict[str, list[str]] = {
    "vestido": ["zapatos de tacón elegantes", "cartera de mano", "collares"],
    "jean": ["polo básico", "hoodie casual", "zapatillas urbanas"],
    "polo": ["jeans clásicos", "casaca ligera", "zapatillas"],
    "chompa": ["jeans oscuros", "botas", "gorro de lana"],
    "casaca": ["polo cuello alto", "jeans", "zapatos casuales"],
    "vestido elegante": ["tacones", "cartera clutch", "chal", "joyería fina"],
    "pantalon formal": ["camisa manga larga", "corbata", "zapatos formal"],
}


class RecommendationEngine:
    def __init__(self, product_context: ProductContextEngine) -> None:
        self._product_context = product_context

    async def generate_recommendations(
        self,
        *,
        empresa_id: UUID,
        current_product_category: str | None = None,
        current_product_type: str | None = None,
    ) -> list[Recommendation]:
        related = []
        seen = set()
        upsell_categories = UPSELL_MAP.get(current_product_type or "", [])
        if current_product_category:
            upsell_categories.append(current_product_category)

        for cat in upsell_categories:
            if cat in seen:
                continue
            seen.add(cat)
            products = await self._product_context.get_related_products(
                empresa_id=empresa_id,
                product_category=cat.capitalize(),
                limit=3,
            )
            if products:
                related.append(
                    Recommendation(
                        category=cat,
                        suggestion=f"También tenemos {cat} que combinan perfecto",
                        products_count=len(products),
                    )
                )
        return related

    async def get_upsell_text(
        self,
        *,
        empresa_id: UUID,
        product_type: str | None,
        product_category: str | None,
    ) -> str | None:
        if not product_type and not product_category:
            return None

        key = product_type or ""
        if product_category and key:
            key = f"{key} {product_category}".strip()

        if key in COMPLEMENTARY_UPSELLS:
            items = COMPLEMENTARY_UPSELLS[key]
            return "También te recomendaría: " + ", ".join(items) + "."

        fallback = UPSELL_MAP.get(product_type or "", [])
        if fallback:
            return f"¿Te gustaría ver también nuestra colección de {fallback[0]}?"
        return None
