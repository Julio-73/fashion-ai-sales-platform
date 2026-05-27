import logging
from uuid import UUID

from app.smart_sales.product_context import ProductContextEngine

logger = logging.getLogger("ai_sales_agent.smart_sales.reasoning.advanced_recommender")


PREMIUM_UPSELL_MAP: dict[str, list[dict]] = {
    "vestido": [
        {"suggestion": "tacones elegantes", "category": "Zapatos"},
        {"suggestion": "cartera de mano tipo clutch", "category": "Accesorios"},
        {"suggestion": "collares o joyería fina", "category": "Accesorios"},
    ],
    "jean": [
        {"suggestion": "polo básico premium", "category": "Polos"},
        {"suggestion": "hoodie o chompa casual", "category": "Chompas"},
        {"suggestion": "zapatillas urbanas", "category": "Zapatillas"},
    ],
    "pantalon": [
        {"suggestion": "camisa manga larga", "category": "Camisas"},
        {"suggestion": "zapatos formales", "category": "Zapatos"},
        {"suggestion": "cinturón de cuero", "category": "Accesorios"},
    ],
    "chompa": [
        {"suggestion": "jeans oscuros", "category": "Jeans"},
        {"suggestion": "zapatillas casual", "category": "Zapatillas"},
        {"suggestion": "gorro de lana", "category": "Accesorios"},
    ],
    "casaca": [
        {"suggestion": "polo cuello alto", "category": "Polos"},
        {"suggestion": "jeans o pantalones slim", "category": "Jeans"},
        {"suggestion": "botas o zapatos casuales", "category": "Zapatos"},
    ],
    "polo": [
        {"suggestion": "jeans clásicos", "category": "Jeans"},
        {"suggestion": "casaca ligera", "category": "Casacas"},
        {"suggestion": "zapatillas", "category": "Zapatillas"},
    ],
    "camisa": [
        {"suggestion": "pantalones de vestir", "category": "Pantalones"},
        {"suggestion": "zapatos formales", "category": "Zapatos"},
        {"suggestion": "corbata elegante", "category": "Accesorios"},
    ],
    "zapatillas": [
        {"suggestion": "medias deportivas", "category": "Accesorios"},
        {"suggestion": "short deportivo", "category": "Shorts"},
        {"suggestion": "polo deportivo", "category": "Polos"},
    ],
    "short": [
        {"suggestion": "polo o camiseta", "category": "Polos"},
        {"suggestion": "zapatillas", "category": "Zapatillas"},
        {"suggestion": "gorra", "category": "Accesorios"},
    ],
    "falda": [
        {"suggestion": "blusa o top", "category": "Polos"},
        {"suggestion": "zapatos elegantes", "category": "Zapatos"},
        {"suggestion": "cartera pequeña", "category": "Accesorios"},
    ],
    "accesorio": [
        {"suggestion": "vestidos que combinan", "category": "Vestidos"},
        {"suggestion": "polos elegantes", "category": "Polos"},
    ],
}


class AdvancedRecommender:
    def __init__(self, product_context: ProductContextEngine) -> None:
        self._product_context = product_context

    async def get_premium_upsell_text(
        self,
        *,
        empresa_id: UUID,
        product_type: str | None,
    ) -> str | None:
        if not product_type:
            return None
        upsells = PREMIUM_UPSELL_MAP.get(product_type)
        if not upsells:
            return None

        chosen = upsells[:2]
        items = [u["suggestion"] for u in chosen]
        return f"Te recomendaría combinarlo con {items[0]}{' y ' + items[1] if len(items) > 1 else ''} 👌"

    async def get_more_like_this(
        self,
        *,
        empresa_id: UUID,
        category: str | None,
        product_id: str | None,
        limit: int = 3,
    ) -> list:
        if not category and not product_id:
            return []
        related = await self._product_context.get_related_products(
            empresa_id=empresa_id,
            product_category=category,
            limit=limit,
        )
        return related
