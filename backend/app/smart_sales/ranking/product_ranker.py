import logging

from app.smart_sales.product_matcher import MatchedProduct
from app.smart_sales.entity_extractor import PRODUCT_ALIASES, COLOR_ALIASES, STYLE_ALIASES, OCCASION_ALIASES

logger = logging.getLogger("ai_sales_agent.smart_sales.ranking.product_ranker")


class ProductRankingEngine:
    def rank_products(
        self,
        products: list[MatchedProduct],
        entities: dict,
        memory_context: str | None = None,
    ) -> list[MatchedProduct]:
        scored = []
        for product in products:
            score = self._compute_v2_score(product, entities, memory_context)
            scored.append((score, product))
        scored.sort(key=lambda x: x[0], reverse=True)
        for s, p in scored:
            p.score = s
        return [p for _, p in scored]

    def _compute_v2_score(
        self,
        product: MatchedProduct,
        entities: dict,
        memory_context: str | None = None,
    ) -> float:
        score = 0.0
        name_lower = product.name.lower()
        category_lower = (product.category or "").lower()

        # Category match (weight: 30)
        if entities.get("product_type"):
            aliases = PRODUCT_ALIASES.get(entities["product_type"], [entities["product_type"]])
            if any(a in category_lower or a in name_lower for a in aliases):
                score += 30.0
            else:
                score -= 5.0

        # Color match (weight: 20)
        if entities.get("color"):
            color_variants = [c for c, v in COLOR_ALIASES.items() if v == entities["color"]]
            if entities["color"].lower() in name_lower:
                score += 20.0
            elif any(v in name_lower for v in color_variants):
                score += 18.0
            elif product.available_colors:
                product_colors_lower = [c.lower() for c in product.available_colors]
                if entities["color"].lower() in product_colors_lower:
                    score += 20.0
                else:
                    score -= 3.0

        # Size match (weight: 15)
        if entities.get("size") and product.available_sizes:
            if entities["size"].upper() in [s.upper() for s in product.available_sizes]:
                score += 15.0
            else:
                score -= 5.0

        # Gender match (weight: 10)
        if entities.get("gender"):
            gender_terms = {
                "hombre": ["hombre", "men", "man", "masculino"],
                "mujer": ["mujer", "woman", "women", "femenino", "dama"],
                "unisex": ["unisex"],
            }
            terms = gender_terms.get(entities["gender"], [entities["gender"]])
            if any(t in name_lower or t in category_lower for t in terms):
                score += 10.0

        # Style match (weight: 10)
        if entities.get("style"):
            style_words = STYLE_ALIASES.get(entities["style"], [entities["style"]])
            if any(s in name_lower or s in category_lower for s in style_words):
                score += 10.0

        # Occasion match (weight: 10)
        if entities.get("occasion"):
            occ_words = OCCASION_ALIASES.get(entities["occasion"], [entities["occasion"]])
            if any(o in name_lower or o in category_lower for o in occ_words):
                score += 10.0

        # Stock bonus (weight: 10)
        total_stock = product.total_available_stock
        if total_stock > 0:
            score += min(total_stock / 10.0, 10.0)
        else:
            score -= 10.0

        # Textual fuzzy score from product matcher (weight: 10)
        score += product.score * 0.1

        # Memory context boost
        if memory_context:
            words = memory_context.lower().split()
            matches = sum(1 for w in words if w in name_lower or w in category_lower)
            score += min(matches * 2.0, 8.0)

        return round(score, 1)
