from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from app.ai.intelligence.churn_risk_detector import ChurnRiskDetector
from app.ai.intelligence.conversion_predictor import ConversionPredictor
from app.ai.intelligence.customer_behavior_analyzer import CustomerBehaviorAnalyzer
from app.ai.intelligence.purchase_pattern_detector import PurchasePatternDetector
from app.ai.intelligence.recommendation_context_engine import (
    RecommendationContextEngine,
)


@pytest.fixture
def mock_session() -> AsyncMock:
    return AsyncMock()


class TestCustomerBehaviorAnalyzer:
    EMPRESA_ID = UUID("00000000-0000-0000-0000-000000000001")
    CUSTOMER_ID = UUID("00000000-0000-0000-0000-000000000002")

    def test_analyzer_creation(self, mock_session):
        analyzer = CustomerBehaviorAnalyzer(mock_session)
        assert analyzer is not None

    async def test_detect_hot_customers(self, mock_session):
        analyzer = CustomerBehaviorAnalyzer(mock_session)
        with patch.object(analyzer._sales_repo, "is_hot_lead", AsyncMock(return_value=True)):
            with patch.object(analyzer._sales_repo, "get_buying_intent_trend", AsyncMock(return_value="increasing")):
                with patch.object(analyzer._sales_repo, "get_conversion_probability", AsyncMock(return_value="high")):
                    hot = await analyzer.detect_hot_customers(
                        empresa_id=self.EMPRESA_ID,
                        customer_ids=[self.CUSTOMER_ID],
                    )

        assert len(hot) == 1
        assert hot[0]["is_hot"] is True
        assert hot[0]["trend"] == "increasing"

    async def test_detect_discount_sensitivity(self, mock_session):
        analyzer = CustomerBehaviorAnalyzer(mock_session)
        with patch.object(analyzer._sales_repo, "get_discount_sensitivity", AsyncMock(return_value="high")):
            sensitive = await analyzer.detect_discount_sensitivity(
                empresa_id=self.EMPRESA_ID,
                customer_ids=[self.CUSTOMER_ID],
            )
        assert len(sensitive) == 1
        assert sensitive[0]["discount_sensitivity"] == "high"


class TestConversionPredictor:
    EMPRESA_ID = UUID("00000000-0000-0000-0000-000000000001")

    async def test_predict_conversion_returns_structure(self, mock_session):
        predictor = ConversionPredictor(mock_session)
        mock_customer = MagicMock()
        mock_customer.lead_score = 45
        mock_customer.priority = "warm"
        mock_customer.lead_status = "interested"
        mock_customer.last_interaction_at = None
        mock_customer.deleted_at = None

        with patch.object(predictor, "_get_customer", AsyncMock(return_value=mock_customer)):
            with patch.object(predictor._sales_repo, "get_conversion_probability", AsyncMock(return_value="medium")):
                with patch.object(predictor._sales_repo, "get_buying_intent_trend", AsyncMock(return_value="stable")):
                    with patch.object(predictor._sales_repo, "get_churn_risk", AsyncMock(return_value="low")):
                        with patch.object(predictor._sales_repo, "get_negotiation_stage", AsyncMock(return_value="engaged")):
                            result = await predictor.predict_conversion(
                                empresa_id=self.EMPRESA_ID,
                                customer_id=UUID("00000000-0000-0000-0000-000000000002"),
                            )

        assert "probability" in result
        assert "score" in result
        assert "factors" in result
        assert result["score"] == 45

    async def test_predict_conversion_unknown_customer(self, mock_session):
        predictor = ConversionPredictor(mock_session)
        with patch.object(predictor, "_get_customer", AsyncMock(return_value=None)):
            result = await predictor.predict_conversion(
                empresa_id=self.EMPRESA_ID,
                customer_id=UUID("00000000-0000-0000-0000-000000009999"),
            )
        assert result["probability"] == "low"
        assert result["score"] == 0


class TestPurchasePatternDetector:
    EMPRESA_ID = UUID("00000000-0000-0000-0000-000000000001")

    async def test_detect_patterns_returns_dict(self, mock_session):
        detector = PurchasePatternDetector(mock_session)
        from unittest.mock import MagicMock
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        result = await detector.detect_patterns(
            empresa_id=self.EMPRESA_ID,
            customer_id=UUID("00000000-0000-0000-0000-000000000002"),
        )
        assert "detected_patterns" in result
        assert "total_patterns" in result
        assert isinstance(result["detected_patterns"], dict)

    async def test_seasonal_preferences(self, mock_session):
        detector = PurchasePatternDetector(mock_session)
        from unittest.mock import MagicMock
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        result = await detector.detect_seasonal_preferences(
            empresa_id=self.EMPRESA_ID,
            customer_id=UUID("00000000-0000-0000-0000-000000000002"),
        )
        assert "detected_seasons" in result
        assert "primary_season" in result


class TestChurnRiskDetector:
    EMPRESA_ID = UUID("00000000-0000-0000-0000-000000000001")

    async def test_evaluate_churn_returns_risk(self, mock_session):
        detector = ChurnRiskDetector(mock_session)
        mock_customer = MagicMock()
        mock_customer.last_interaction_at = None
        mock_customer.lead_score = 3
        mock_customer.lead_status = "new"
        mock_customer.priority = "cold"
        mock_customer.conversation_count = 0
        mock_customer.deleted_at = None

        with patch.object(detector, "_get_customer", AsyncMock(return_value=mock_customer)):
            result = await detector.evaluate_churn(
                empresa_id=self.EMPRESA_ID,
                customer_id=UUID("00000000-0000-0000-0000-000000000002"),
            )

        assert "risk" in result
        assert "risk_score" in result
        assert "factors" in result

    async def test_get_at_risk_customers(self, mock_session):
        detector = ChurnRiskDetector(mock_session)
        from unittest.mock import MagicMock as MM
        mock_result = MM()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        result = await detector.get_at_risk_customers(
            empresa_id=self.EMPRESA_ID
        )
        assert isinstance(result, list)


class TestRecommendationContextEngine:
    EMPRESA_ID = UUID("00000000-0000-0000-0000-000000000001")

    async def test_build_full_intelligence(self, mock_session):
        engine = RecommendationContextEngine(mock_session)
        mock_rich = MagicMock()
        mock_rich.model_dump.return_value = {"test": "data"}
        mock_rich.sales.is_hot_lead = True
        mock_rich.sales.is_premium_customer = False

        with patch.object(engine._real_context, "build_rich_context", AsyncMock(return_value=mock_rich)):
            with patch.object(engine._conversion, "predict_conversion", AsyncMock(return_value={"probability": "high"})):
                with patch.object(engine._patterns, "detect_patterns", AsyncMock(return_value={"detected_patterns": {}})):
                    with patch.object(engine._churn, "evaluate_churn", AsyncMock(return_value={"risk": "low"})):
                        with patch.object(engine._patterns, "detect_seasonal_preferences", AsyncMock(return_value={"detected_seasons": {}})):
                            result = await engine.build_full_intelligence(
                                empresa_id=self.EMPRESA_ID,
                                customer_id=UUID("00000000-0000-0000-0000-000000000002"),
                                conversation_id=UUID("00000000-0000-0000-0000-000000000003"),
                            )

        assert "rich_context" in result
        assert "conversion_prediction" in result
        assert "purchase_patterns" in result
        assert "churn_risk" in result
        assert "recommended_next_action" in result
        assert "IMMEDIATE" in result["recommended_next_action"]
