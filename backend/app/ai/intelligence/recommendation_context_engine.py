import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.context.services.real_context_builder import RealContextBuilder
from app.ai.intelligence.churn_risk_detector import ChurnRiskDetector
from app.ai.intelligence.conversion_predictor import ConversionPredictor
from app.ai.intelligence.customer_behavior_analyzer import CustomerBehaviorAnalyzer
from app.ai.intelligence.purchase_pattern_detector import PurchasePatternDetector

logger = logging.getLogger("ai_sales_agent.ai.intelligence.recommendation_context")


class RecommendationContextEngine:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._real_context = RealContextBuilder(session)
        self._behavior = CustomerBehaviorAnalyzer(session)
        self._conversion = ConversionPredictor(session)
        self._patterns = PurchasePatternDetector(session)
        self._churn = ChurnRiskDetector(session)

    async def build_full_intelligence(
        self,
        *,
        empresa_id: UUID,
        customer_id: UUID,
        conversation_id: UUID,
    ) -> dict:
        rich_context = await self._real_context.build_rich_context(
            empresa_id=empresa_id,
            customer_id=customer_id,
            conversation_id=conversation_id,
        )
        conversion = await self._conversion.predict_conversion(
            empresa_id=empresa_id, customer_id=customer_id
        )
        patterns = await self._patterns.detect_patterns(
            empresa_id=empresa_id, customer_id=customer_id
        )
        churn = await self._churn.evaluate_churn(
            empresa_id=empresa_id, customer_id=customer_id
        )
        seasonal = await self._patterns.detect_seasonal_preferences(
            empresa_id=empresa_id, customer_id=customer_id
        )

        return {
            "rich_context": rich_context.model_dump(),
            "conversion_prediction": conversion,
            "purchase_patterns": patterns,
            "churn_risk": churn,
            "seasonal_preferences": seasonal,
            "is_hot": rich_context.sales.is_hot_lead,
            "is_premium": rich_context.sales.is_premium_customer,
            "recommended_next_action": self._recommend_action(rich_context, conversion, churn),
        }

    def _recommend_action(self, rich_context, conversion: dict, churn: dict) -> str:
        sales = rich_context.sales
        if churn.get("risk") == "high":
            return "REACTIVATION: Enviar campaña de re-engagement con oferta especial"
        if sales.is_hot_lead:
            return "IMMEDIATE: Contactar urgente para cierre de venta"
        if sales.is_premium_customer:
            return "UPSELL: Ofrecer productos premium y colección exclusiva"
        if conversion.get("probability") == "high":
            return "CLOSE: Preparar propuesta final y enviar a cierre"
        if sales.discount_sensitivity == "high":
            return "DISCOUNT: Ofrecer descuento personalizado para incentivar compra"
        if churn.get("risk") == "medium":
            return "ENGAGE: Enviar contenido relevante y nuevos productos"
        return "NURTURE: Mantener seguimiento regular con contenido de valor"
