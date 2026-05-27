import logging
from dataclasses import dataclass

from app.smart_sales.product_matcher import MatchedProduct

logger = logging.getLogger("ai_sales_agent.smart_sales.reasoning.confidence")


@dataclass
class ConfidenceResult:
    score: float
    level: str  # "high", "medium", "low"
    reason: str

    def should_ask_before_recommend(self) -> bool:
        return self.level == "low"

    def should_recommend_directly(self) -> bool:
        return self.level in ("high", "medium")


class ConfidenceScorer:
    def evaluate(
        self,
        *,
        entities: dict,
        matched_products: list[MatchedProduct],
        has_history: bool,
    ) -> ConfidenceResult:
        score = 0.0
        reasons = []

        if entities.get("product_type"):
            score += 25.0
            reasons.append("product_type detectado")

        if entities.get("color"):
            score += 15.0
            reasons.append("color detectado")

        if entities.get("size"):
            score += 10.0
            reasons.append("talla detectada")

        if entities.get("style"):
            score += 10.0
            reasons.append("estilo detectado")

        if entities.get("gender"):
            score += 10.0
            reasons.append("género detectado")

        if entities.get("occasion"):
            score += 10.0
            reasons.append("ocasión detectada")

        if has_history:
            score += 10.0
            reasons.append("historial disponible")

        if matched_products:
            top_score = matched_products[0].score
            score += min(top_score * 0.3, 20.0)
            if matched_products[0].has_stock:
                score += 10.0
                reasons.append("stock disponible")

            has_color_match = entities.get("color") and any(
                entities["color"].lower() in p.name.lower() for p in matched_products[:3]
            )
            if has_color_match:
                score += 5.0
                reasons.append("color coincide con productos")

        if not entities.get("product_type") and not entities.get("color") and not entities.get("style"):
            score = 5.0
            reasons = ["poca información del cliente"]

        score = min(score, 100.0)

        if score >= 60:
            level = "high"
        elif score >= 30:
            level = "medium"
        else:
            level = "low"

        return ConfidenceResult(score=round(score, 1), level=level, reason=", ".join(reasons))
