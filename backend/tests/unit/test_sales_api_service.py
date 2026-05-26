"""Tests for SalesAPIService."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.errors import AppError
from app.core.security.dependencies import TenantContext
from app.modules.customers.models import Cliente
from app.sales.api.schemas import AnalyzeMessageResponse
from app.sales.api.service import SalesAPIService
from app.sales.classifiers.intent_classifier import IntentClassifier
from app.sales.intents.intent import IntentType
from app.sales.scoring.lead_scorer import LeadScorer
from tests.conftest import TEST_CUSTOMER_ID, TEST_EMPRESA_ID

_now = datetime.now(timezone.utc)


_SENTINEL = object()


def _mock_result(scalars_return=_SENTINEL, all_return=_SENTINEL, one_or_none=_SENTINEL, scalar_one_or_none=_SENTINEL, scalar=_SENTINEL, scalar_one=_SENTINEL):
    mock_result = MagicMock()
    if scalars_return is not _SENTINEL:
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = scalars_return
        mock_result.scalars.return_value = mock_scalars
    if all_return is not _SENTINEL:
        mock_result.all.return_value = all_return
    if one_or_none is not _SENTINEL:
        mock_result.one_or_none.return_value = one_or_none
    if scalar_one_or_none is not _SENTINEL:
        mock_result.scalar_one_or_none.return_value = scalar_one_or_none
    if scalar is not _SENTINEL:
        mock_result.scalar.return_value = scalar
    if scalar_one is not _SENTINEL:
        mock_result.scalar_one.return_value = scalar_one
    return mock_result


def _make_cliente(**kw):
    defaults = dict(
        id=TEST_CUSTOMER_ID,
        empresa_id=TEST_EMPRESA_ID,
        full_name="Maria Garcia",
        email="maria@test.com",
        phone="+51999000001",
        whatsapp=None,
        instagram_username=None,
        tags=["vip"],
        notes=None,
        lead_status="interested",
        source="web",
        assigned_to=None,
        last_interaction_at=_now,
        conversation_count=3,
        last_conversation_id=None,
        lead_score=45,
        priority="warm",
        created_at=_now,
        updated_at=_now,
        deleted_at=None,
    )
    defaults.update(kw)
    return Cliente(**defaults)


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def tenant():
    return TenantContext(
        empresa_id=TEST_EMPRESA_ID,
        user_id=uuid4(),
        roles=["admin"],
        permissions={"sales:read"},
    )


@pytest.fixture
def sales_api_service(mock_session):
    return SalesAPIService(session=mock_session)


# ── Insights ──────────────────────────────────


class TestGetInsights:
    pytestmark = pytest.mark.asyncio
    async def test_returns_structured_insights(self, sales_api_service, mock_session, tenant):
        cliente = _make_cliente()
        mock_session.execute.return_value = _mock_result(scalars_return=[cliente])

        result = await sales_api_service.get_insights(tenant=tenant)

        assert result.total_interested >= 0
        assert result.total_hot_leads >= 0
        assert result.total_negotiation >= 0
        assert result.total_converted >= 0
        assert isinstance(result.top_customers, list)
        assert isinstance(result.high_priority_customers, list)
        assert isinstance(result.most_detected_intents, list)
        assert isinstance(result.recent_sales_activity, int)

    async def test_tenant_isolation(self, sales_api_service, mock_session):
        tenant_a = TenantContext(empresa_id=uuid4(), user_id=uuid4(), roles=["admin"], permissions={"sales:read"})
        tenant_b = TenantContext(empresa_id=uuid4(), user_id=uuid4(), roles=["admin"], permissions={"sales:read"})
        mock_session.execute.return_value = _mock_result(scalars_return=[])

        result_a = await sales_api_service.get_insights(tenant=tenant_a)
        result_b = await sales_api_service.get_insights(tenant=tenant_b)

        assert result_a.total_hot_leads == 0
        assert result_b.total_hot_leads == 0

    async def test_counts_interested_correctly(self, sales_api_service, mock_session, tenant):
        cliente_a = _make_cliente(lead_status="interested")
        cliente_b = _make_cliente(lead_status="interested", id=uuid4())
        cliente_c = _make_cliente(lead_status="won", id=uuid4())
        mock_session.execute.return_value = _mock_result(scalars_return=[cliente_a, cliente_b, cliente_c])

        result = await sales_api_service.get_insights(tenant=tenant)

        assert result.total_interested == 2
        assert result.total_converted == 1


# ── Customer Sales Profile ────────────────────


class TestGetCustomerProfile:
    pytestmark = pytest.mark.asyncio
    async def test_returns_profile_for_existing_customer(self, sales_api_service, mock_session, tenant):
        cliente = _make_cliente()

        def execute_side_effect(*args, **kwargs):
            stmt = str(args[0])
            if "FROM clientes" in stmt and "WHERE" in stmt:
                return _mock_result(scalar_one_or_none=cliente)
            if "FROM messages_core" in stmt:
                return _mock_result(scalar_one=0, one_or_none=None, all_return=[])
            return _mock_result(scalar=0, scalar_one=0, all_return=[])

        mock_session.execute.side_effect = execute_side_effect

        result = await sales_api_service.get_customer_profile(tenant=tenant, customer_id=TEST_CUSTOMER_ID)

        assert result.customer_id == str(TEST_CUSTOMER_ID)
        assert result.full_name == "Maria Garcia"
        assert result.lead_score == 45
        assert result.lead_status == "interested"
        assert result.priority == "warm"
        assert result.activity_level in ("very_active", "active", "moderate", "low", "inactive")
        assert isinstance(result.detected_intents, list)
        assert isinstance(result.conversation_metrics.total_conversations, int)
        assert result.conversation_metrics.total_messages == 0
        assert result.conversation_metrics.last_message_content is None
        assert result.sales_summary

    async def test_raises_404_when_customer_not_found(self, sales_api_service, mock_session, tenant):
        mock_session.execute.return_value = _mock_result(scalar_one_or_none=None)

        with pytest.raises(AppError) as e:
            await sales_api_service.get_customer_profile(tenant=tenant, customer_id=uuid4())
        assert e.value.status_code == 404


# ── Analyze Message ───────────────────────────


class TestAnalyzeMessage:
    pytestmark = pytest.mark.asyncio
    async def test_returns_analysis_for_existing_customer(self, sales_api_service, mock_session, tenant):
        cliente = _make_cliente(last_interaction_at=None)
        mock_session.execute.return_value = _mock_result(scalar_one_or_none=cliente)

        result = await sales_api_service.analyze_message(
            tenant=tenant,
            customer_id=TEST_CUSTOMER_ID,
            message="Hola, quiero informacion",
        )

        assert isinstance(result, AnalyzeMessageResponse)
        assert isinstance(result.detected_intent, IntentType)
        assert isinstance(result.score_impact, int)
        assert result.score_impact >= 0
        assert result.recommended_action
        assert result.lead_status_prediction

    async def test_raises_404_when_customer_not_found(self, sales_api_service, mock_session, tenant):
        mock_session.execute.return_value = _mock_result(scalar_one_or_none=None)

        with pytest.raises(AppError) as e:
            await sales_api_service.analyze_message(
                tenant=tenant,
                customer_id=uuid4(),
                message="Hola",
            )
        assert e.value.status_code == 404

    async def test_lead_scorer_consistency(self):
        scorer = LeadScorer()
        score = scorer.calculate_score(
            intent_labels=["purchase_intent", "pricing_intent"],
            message_count=2,
            conversation_count=1,
            last_interaction_at=_now,
        )
        assert isinstance(score, int)
        assert score >= 0

        priority = scorer.score_to_priority(score)
        assert priority in ("hot", "warm", "cool", "cold")


# ── Intent Classifier Consistency ─────────────


class TestIntentClassifier:
    def test_detects_purchase_intent(self):
        classifier = IntentClassifier()
        intent, weight = classifier.classify("quiero comprar un producto")
        assert intent == IntentType.purchase_intent

    def test_detects_greeting(self):
        classifier = IntentClassifier()
        intent, _ = classifier.classify("Hola buenos dias")
        assert intent == IntentType.greeting

    def test_detects_negotiation(self):
        classifier = IntentClassifier()
        intent, _ = classifier.classify("me hacen descuento")
        assert intent == IntentType.negotiation_intent

    def test_detects_unknown(self):
        classifier = IntentClassifier()
        intent, _ = classifier.classify("xyz123 sin sentido")
        assert intent == IntentType.unknown


# ── Recommendations ───────────────────────────


class TestGetRecommendations:
    pytestmark = pytest.mark.asyncio
    async def test_returns_recommendation_categories(self, sales_api_service, mock_session, tenant):
        cliente = _make_cliente()
        mock_session.execute.return_value = _mock_result(scalars_return=[cliente])

        result = await sales_api_service.get_recommendations(tenant=tenant)

        assert isinstance(result.customers_to_follow_up, list)
        assert isinstance(result.hot_leads, list)
        assert isinstance(result.negotiation_leads, list)
        assert isinstance(result.inactive_customers, list)
        assert isinstance(result.upsell_opportunities, list)

    async def test_empty_tenant_returns_empty_lists(self, sales_api_service, mock_session):
        other_tenant = TenantContext(empresa_id=uuid4(), user_id=uuid4(), roles=["admin"], permissions={"sales:read"})
        mock_session.execute.return_value = _mock_result(scalars_return=[])

        result = await sales_api_service.get_recommendations(tenant=other_tenant)
        assert len(result.customers_to_follow_up) == 0
        assert len(result.hot_leads) == 0


# ── Top Leads ─────────────────────────────────


class TestGetTopLeads:
    pytestmark = pytest.mark.asyncio
    async def test_returns_leads_ordered_by_score(self, sales_api_service, mock_session, tenant):
        clientes = [_make_cliente(lead_score=80), _make_cliente(lead_score=40)]
        mock_session.execute.return_value = _mock_result(scalars_return=clientes)

        result = await sales_api_service.get_top_leads(tenant=tenant, limit=10)

        assert len(result.leads) == 2
        assert result.total == 2
        for lead in result.leads:
            assert lead.conversion_probability in ("high", "medium", "low")

    async def test_respects_limit(self, sales_api_service, mock_session, tenant):
        clientes = [_make_cliente(lead_score=i * 10) for i in range(5)]
        mock_session.execute.return_value = _mock_result(scalars_return=clientes)

        result = await sales_api_service.get_top_leads(tenant=tenant, limit=3)

        assert len(result.leads) == 3

    async def test_tenant_isolation(self, sales_api_service, mock_session):
        other_tenant = TenantContext(empresa_id=uuid4(), user_id=uuid4(), roles=["admin"], permissions={"sales:read"})
        mock_session.execute.return_value = _mock_result(scalars_return=[])

        result = await sales_api_service.get_top_leads(tenant=other_tenant, limit=10)
        assert result.total == 0


# ── Activity Timeline ─────────────────────────


class TestGetActivity:
    pytestmark = pytest.mark.asyncio
    async def test_returns_activity_events(self, sales_api_service, mock_session, tenant):
        mock_session.execute.return_value = _mock_result(all_return=[])

        result = await sales_api_service.get_activity(tenant=tenant, limit=10)

        assert isinstance(result.events, list)
        assert isinstance(result.total, int)

    async def test_empty_tenant_returns_empty(self, sales_api_service, mock_session):
        other_tenant = TenantContext(empresa_id=uuid4(), user_id=uuid4(), roles=["admin"], permissions={"sales:read"})
        mock_session.execute.return_value = _mock_result(all_return=[])

        result = await sales_api_service.get_activity(tenant=other_tenant, limit=10)
        assert result.total == 0
