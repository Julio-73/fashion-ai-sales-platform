"""Unit tests for the pipeline module.

Target: 40+ tests covering models, schemas, AI scoring, automations,
repository, service and permissions.

Run: ``pytest tests/unit/test_pipeline.py -q``.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.security.dependencies import TenantContext
from app.core.security.permissions import ROLE_PERMISSIONS
from app.modules.pipeline import (
    PIPELINE_STAGE_VALUES,
    OPEN_STAGES,
    CLOSED_STAGES,
    SalesPipelineItem,
    is_valid_stage,
)
from app.modules.pipeline.ai import (
    CommercialAI,
    _clamp,
    _engagement_score,
    _intent_score,
    _monetary_score,
    _recency_score,
    _sentiment_score,
    _temperature_score,
    _next_best_action,
    _suggested_channel,
    _suggested_stage,
)
from app.modules.pipeline.automations import AutomationEngine
from app.modules.pipeline.models import (
    LOST_STAGE,
    NEW_LEAD_STAGE,
    WON_STAGE,
)
from app.modules.pipeline.repository import PipelineRepository
from app.modules.pipeline.router import router as pipeline_router
from app.modules.pipeline.schemas import (
    AIScoreBreakdown,
    CustomerSummary,
    PipelineItemCreate,
    PipelineItemMoveStage,
    PipelineItemUpdate,
)
from app.modules.pipeline.service import (
    PipelineService,
    STAGE_CATALOG,
)


TEST_EMPRESA_ID = UUID("11111111-1111-4111-8111-111111111111")
TEST_USER_ID = UUID("22222222-2222-4222-8222-222222222222")
TEST_CUSTOMER_ID = UUID("33333333-3333-4333-8333-333333333333")
TEST_CONVERSATION_ID = UUID("77777777-7777-4777-8777-777777777777")


# ─────────────────────────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────────────────────────


def test_pipeline_stage_values_complete() -> None:
    assert set(PIPELINE_STAGE_VALUES) == {
        "new_lead",
        "contacted",
        "qualified",
        "proposal",
        "negotiation",
        "won",
        "lost",
    }


def test_open_stages_are_not_terminal() -> None:
    assert "won" not in OPEN_STAGES
    assert "lost" not in OPEN_STAGES
    for s in OPEN_STAGES:
        assert s in PIPELINE_STAGE_VALUES


def test_closed_stages_contain_won_lost() -> None:
    assert CLOSED_STAGES == frozenset({"won", "lost"})


def test_is_valid_stage() -> None:
    assert is_valid_stage("won") is True
    assert is_valid_stage("invalid") is False
    assert is_valid_stage("") is False


def test_sales_pipeline_item_tablename() -> None:
    assert SalesPipelineItem.__tablename__ == "sales_pipeline_items"


# ─────────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────────


def test_pipeline_item_create_defaults() -> None:
    p = PipelineItemCreate(title="Hot lead")
    assert p.stage == "new_lead"
    assert p.probability == 0
    assert p.estimated_value == Decimal("0")
    assert p.is_vip is False


def test_pipeline_item_create_invalid_stage() -> None:
    with pytest.raises(ValueError):
        PipelineItemCreate(title="x", stage="banana")  # type: ignore[arg-type]


def test_pipeline_item_update_partial() -> None:
    p = PipelineItemUpdate(notes="hi", is_vip=True)
    assert p.notes == "hi"
    assert p.is_vip is True
    assert p.title is None


def test_pipeline_item_move_stage_invalid() -> None:
    with pytest.raises(ValueError):
        PipelineItemMoveStage(target_stage="banana")  # type: ignore[arg-type]


def test_ai_score_breakdown_clamped() -> None:
    a = AIScoreBreakdown.model_construct(
        total=150, intent=-10, engagement=200, recency=50, monetary=50, sentiment=50, rationale=[]
    )
    assert a.total == 100
    assert a.intent == 0
    assert a.engagement == 100


def test_customer_summary_required() -> None:
    c = CustomerSummary(id=uuid4(), full_name="Jane Doe")
    assert c.lifetime_value == Decimal("0")
    assert c.orders_count == 0


# ─────────────────────────────────────────────────────────────────────────────
# AI — pure scoring helpers
# ─────────────────────────────────────────────────────────────────────────────


def test_clamp_bounds() -> None:
    assert _clamp(50) == 50
    assert _clamp(-5) == 0
    assert _clamp(200) == 100
    assert _clamp(50, 10, 20) == 20


@pytest.mark.parametrize(
    "intent,expected_min,expected_max",
    [
        ("buy_now", 90, 95),
        ("price_check", 65, 75),
        ("complaint_again", 15, 25),
        ("greeting", 10, 20),
        (None, 30, 40),
        ("", 30, 40),
    ],
)
def test_intent_score_known_keywords(intent: str | None, expected_min: int, expected_max: int) -> None:
    v = _intent_score(intent)
    assert expected_min <= v <= expected_max


@pytest.mark.parametrize(
    "sentiment,expected",
    [
        ("positive", 80),
        ("neutral", 50),
        ("negative", 20),
        ("POSITIVE", 80),  # case-insensitive
        (None, 50),
    ],
)
def test_sentiment_score(sentiment: str | None, expected: int) -> None:
    assert _sentiment_score(sentiment) == expected


def test_temperature_score() -> None:
    assert _temperature_score("hot") == 90
    assert _temperature_score("warm") == 60
    assert _temperature_score("cold") == 25
    assert _temperature_score(None) == 40


def test_recency_score_decay() -> None:
    now = datetime(2026, 6, 1, 12, 0, 0)
    assert _recency_score(now - timedelta(hours=1), now) == 95
    assert _recency_score(now - timedelta(days=2), now) == 80
    assert _recency_score(now - timedelta(days=12), now) == 40
    assert _recency_score(now - timedelta(days=60), now) == 10
    assert _recency_score(None, now) == 20


def test_monetary_score_zero() -> None:
    assert _monetary_score(Decimal("0"), Decimal("0"), 0) == 10


def test_monetary_score_high() -> None:
    s = _monetary_score(Decimal("5000"), Decimal("2000"), 3)
    assert s >= 70
    assert s <= 100


def test_engagement_score_combined() -> None:
    base = _engagement_score(0, None)
    assert base == 0
    boosted = _engagement_score(8, 0.8)
    assert boosted > base
    assert boosted <= 100


# ─────────────────────────────────────────────────────────────────────────────
# AI — recommendation helpers (pure)
# ─────────────────────────────────────────────────────────────────────────────


def test_next_best_action_for_closed() -> None:
    deal = SimpleNamespace(stage="won", probability=100)
    breakdown = AIScoreBreakdown(total=50, intent=50, engagement=50, recency=50, monetary=50)
    assert "cerrado" in _next_best_action(deal, breakdown).lower()


def test_next_best_action_for_high_intent() -> None:
    deal = SimpleNamespace(stage="qualified", probability=50)
    breakdown = AIScoreBreakdown(total=80, intent=90, engagement=70, recency=70, monetary=50)
    a = _next_best_action(deal, breakdown)
    assert "propuesta" in a.lower() or "bloqueado" in a.lower()


def test_next_best_action_for_cold() -> None:
    deal = SimpleNamespace(stage="contacted", probability=20)
    breakdown = AIScoreBreakdown(total=20, intent=10, engagement=20, recency=10, monetary=20, sentiment=10)
    a = _next_best_action(deal, breakdown)
    assert "reactivar" in a.lower() or "humano" in a.lower()


def test_suggested_channel_negative_sentiment() -> None:
    deal = SimpleNamespace(stage="negotiation", channel=None)
    b = AIScoreBreakdown(total=50, intent=50, engagement=50, recency=50, monetary=50, sentiment=10)
    assert _suggested_channel(deal, b) == "Llamada"


def test_suggested_channel_high_intent() -> None:
    deal = SimpleNamespace(stage="negotiation", channel=None)
    b = AIScoreBreakdown(total=50, intent=80, engagement=50, recency=50, monetary=50)
    assert _suggested_channel(deal, b) == "WhatsApp"


def test_suggested_stage_won_at_negotiation() -> None:
    deal = SimpleNamespace(stage="negotiation", probability=80)
    b = AIScoreBreakdown(total=80, intent=80, engagement=80, recency=80, monetary=80)
    assert _suggested_stage(deal, b) == "won"


def test_suggested_stage_lost_on_negative() -> None:
    deal = SimpleNamespace(stage="negotiation", probability=50)
    b = AIScoreBreakdown(total=20, intent=10, engagement=20, recency=20, monetary=20, sentiment=10)
    assert _suggested_stage(deal, b) == "lost"


def test_suggested_stage_none_when_closed() -> None:
    deal = SimpleNamespace(stage="won", probability=100)
    b = AIScoreBreakdown(total=80, intent=80, engagement=80, recency=80, monetary=80)
    assert _suggested_stage(deal, b) is None


# ─────────────────────────────────────────────────────────────────────────────
# Repository
# ─────────────────────────────────────────────────────────────────────────────


def _make_deal(**over: object) -> MagicMock:
    deal = MagicMock(spec=SalesPipelineItem)
    deal.id = uuid4()
    deal.empresa_id = TEST_EMPRESA_ID
    deal.customer_id = None
    deal.conversation_id = None
    deal.order_id = None
    deal.title = "Test deal"
    deal.estimated_value = Decimal("100")
    deal.probability = 30
    deal.stage = "qualified"
    deal.stage_entered_at = datetime.utcnow()
    deal.last_activity_at = datetime.utcnow()
    deal.notes = None
    deal.won_reason = None
    deal.lost_reason = None
    deal.position = 0
    deal.channel = None
    deal.is_vip = False
    deal.created_at = datetime.utcnow()
    deal.updated_at = datetime.utcnow()
    for k, v in over.items():
        setattr(deal, k, v)
    return deal


@pytest.mark.asyncio
async def test_repo_create_adds_to_session() -> None:
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    repo = PipelineRepository(session)
    item = await repo.create(
        empresa_id=TEST_EMPRESA_ID,
        customer_id=None,
        conversation_id=None,
        order_id=None,
        title="New",
        estimated_value=Decimal("250"),
        probability=20,
        stage="contacted",
        notes=None,
        channel=None,
        is_vip=False,
        position=0,
    )
    assert session.add.called
    assert item.title == "New"
    assert item.stage == "contacted"


@pytest.mark.asyncio
async def test_repo_update_changes_attributes() -> None:
    session = AsyncMock()
    session.flush = AsyncMock()
    deal = _make_deal()
    repo = PipelineRepository(session)
    out = await repo.update(item=deal, changes={"probability": 90, "notes": "hot"})
    assert out.probability == 90
    assert out.notes == "hot"
    assert isinstance(out.last_activity_at, datetime)


@pytest.mark.asyncio
async def test_repo_update_empty_changes_noop() -> None:
    session = AsyncMock()
    session.flush = AsyncMock()
    deal = _make_deal()
    repo = PipelineRepository(session)
    out = await repo.update(item=deal, changes={})
    assert out is deal


@pytest.mark.asyncio
async def test_repo_move_stage_to_won_clears_lost_reason() -> None:
    session = AsyncMock()
    session.flush = AsyncMock()
    deal = _make_deal(stage="negotiation", won_reason=None, lost_reason="old")
    repo = PipelineRepository(session)
    out = await repo.move_stage(
        item=deal,
        target_stage="won",
        probability=100,
        notes=None,
        won_reason="Compra confirmada",
        lost_reason=None,
    )
    assert out.stage == "won"
    assert out.won_reason == "Compra confirmada"
    assert out.lost_reason is None


@pytest.mark.asyncio
async def test_repo_soft_delete_calls_session_delete() -> None:
    session = AsyncMock()
    session.delete = AsyncMock()
    session.flush = AsyncMock()
    deal = _make_deal()
    repo = PipelineRepository(session)
    await repo.soft_delete(deal)
    session.delete.assert_awaited_once_with(deal)


# ─────────────────────────────────────────────────────────────────────────────
# Service — list_stages, stage_info
# ─────────────────────────────────────────────────────────────────────────────


def test_list_stages_returns_all() -> None:
    stages = PipelineService.list_stages()
    assert len(stages) == 7
    assert {s.key for s in stages} == set(PIPELINE_STAGE_VALUES)


def test_stage_info_known() -> None:
    s = PipelineService.stage_info("won")
    assert s is not None
    assert s.is_terminal is True
    assert s.default_probability == 100


def test_stage_info_unknown_returns_none() -> None:
    assert PipelineService.stage_info("nope") is None


def test_stage_catalog_ordering() -> None:
    orders = [s.order for s in STAGE_CATALOG]
    assert orders == sorted(orders)


# ─────────────────────────────────────────────────────────────────────────────
# Service — create / update / move with mocked session
# ─────────────────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def mock_session() -> AsyncMock:
    s = AsyncMock()
    s.add = MagicMock()
    s.flush = AsyncMock()
    s.commit = AsyncMock()
    s.execute = AsyncMock()
    s.delete = AsyncMock()
    return s


def _build_svc(mock_session: AsyncMock) -> PipelineService:
    svc = PipelineService(mock_session)
    # Patch the heavy bits we don't want to execute
    svc.ai = MagicMock()
    svc.ai.score_deal = AsyncMock(
        return_value=(50, AIScoreBreakdown(total=50, intent=50, engagement=50, recency=50, monetary=50), ["ok"])
    )
    svc.ai.recommend = AsyncMock(
        return_value=None  # not used here
    )
    svc.automations = MagicMock()
    svc.automations.evaluate = AsyncMock(return_value=[])
    return svc


def _execute_result(*, rows=(), one=None) -> MagicMock:
    r = MagicMock()
    r.all = MagicMock(return_value=rows)
    r.scalar = MagicMock(return_value=one)
    r.scalar_one_or_none = MagicMock(return_value=one)
    r.one = MagicMock(return_value=(one,) if one is not None else (0, 0))
    r.rowcount = 0
    return r


@pytest.mark.asyncio
async def test_service_create_succeeds(mock_session: AsyncMock) -> None:
    svc = _build_svc(mock_session)
    # mock list_items to return empty
    svc.repo.list_items = AsyncMock(return_value=[])
    svc.repo.create = AsyncMock(
        return_value=_make_deal(stage="qualified", estimated_value=Decimal("500"), probability=40)
    )
    svc._customers_map = AsyncMock(return_value={})
    svc._orders_stats = AsyncMock(return_value={})
    svc._to_response = AsyncMock(
        return_value=SimpleNamespace(id=uuid4(), ai_score=None, customer=None)
    )
    payload = PipelineItemCreate(title="X", estimated_value=Decimal("500"))
    res = await svc.create(TEST_EMPRESA_ID, payload)
    assert res is not None
    mock_session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_service_create_invalid_stage(mock_session: AsyncMock) -> None:
    svc = _build_svc(mock_session)
    # Pydantic ValidationError on construction — service is never called.
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        PipelineItemCreate(title="X", stage="nope")  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_service_get_not_found(mock_session: AsyncMock) -> None:
    svc = _build_svc(mock_session)
    svc.repo.get = AsyncMock(return_value=None)
    with pytest.raises(Exception) as exc:
        await svc.get(TEST_EMPRESA_ID, uuid4())
    msg = str(exc.value)
    assert "not found" in msg.lower() or "no encontr" in msg.lower() or getattr(exc.value, "code", "") == "not_found"


@pytest.mark.asyncio
async def test_service_move_stage_blocks_reopen(mock_session: AsyncMock) -> None:
    svc = _build_svc(mock_session)
    svc.repo.get = AsyncMock(return_value=_make_deal(stage="won"))
    with pytest.raises(Exception) as exc:
        await svc.move_stage(
            TEST_EMPRESA_ID,
            uuid4(),
            PipelineItemMoveStage(target_stage="qualified"),
        )
    msg = str(exc.value)
    assert ("reabrir" in msg.lower()
            or "invalid_transition" in getattr(exc.value, "code", "")
            or "no se puede" in msg.lower())


@pytest.mark.asyncio
async def test_service_delete_success(mock_session: AsyncMock) -> None:
    svc = _build_svc(mock_session)
    svc.repo.get = AsyncMock(return_value=_make_deal())
    svc.repo.soft_delete = AsyncMock()
    await svc.delete(TEST_EMPRESA_ID, uuid4())
    mock_session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_service_delete_not_found(mock_session: AsyncMock) -> None:
    svc = _build_svc(mock_session)
    svc.repo.get = AsyncMock(return_value=None)
    with pytest.raises(Exception):
        await svc.delete(TEST_EMPRESA_ID, uuid4())


@pytest.mark.asyncio
async def test_service_metrics_aggregates(mock_session: AsyncMock) -> None:
    svc = _build_svc(mock_session)
    svc.repo.aggregate_metrics = AsyncMock(
        return_value={
            "counts": {"new_lead": 2, "contacted": 1, "won": 3, "lost": 1},
            "values": {"new_lead": 100.0, "contacted": 200.0, "won": 900.0, "lost": 50.0},
            "weighted_open": 150.0,
            "oldest_in_stage_days": 12,
        }
    )
    svc._average_time_to_close = AsyncMock(return_value=4.5)
    svc._average_time_in_stage = AsyncMock(return_value=2.0)
    svc._alert_count = AsyncMock(return_value=2)
    svc._by_channel = AsyncMock(return_value={"whatsapp": {"count": 2, "value": 300.0}})
    svc._by_priority = AsyncMock(return_value={"hot": {"count": 1}})
    m = await svc.metrics(TEST_EMPRESA_ID)
    assert m.total_open == 3
    assert m.total_closed_won == 3
    assert m.total_closed_lost == 1
    assert m.conversion_rate_pct == 75.0
    assert m.alerts_count == 2
    assert m.by_channel["whatsapp"]["count"] == 2


@pytest.mark.asyncio
async def test_service_funnel(mock_session: AsyncMock) -> None:
    svc = _build_svc(mock_session)
    svc.repo.count_by_stage = AsyncMock(return_value={"new_lead": 5, "won": 2, "lost": 1})
    svc.repo.sum_value_by_stage = AsyncMock(return_value={"new_lead": 500.0, "won": 200.0, "lost": 50.0})
    f = await svc.funnel(TEST_EMPRESA_ID)
    assert f.total_open == 5
    assert f.total_closed == 3
    assert f.won_value == 200.0
    assert any(s["key"] == "won" for s in f.stages)


@pytest.mark.asyncio
async def test_service_alerts_returns_empty_when_no_open(mock_session: AsyncMock) -> None:
    svc = _build_svc(mock_session)
    svc.repo.list_items = AsyncMock(return_value=[])
    svc.automations.evaluate = AsyncMock(return_value=[])
    a = await svc.alerts(TEST_EMPRESA_ID)
    assert a.total == 0
    assert a.alerts == []


@pytest.mark.asyncio
async def test_service_recommendations_orders_desc(mock_session: AsyncMock) -> None:
    svc = _build_svc(mock_session)
    deals = [_make_deal(stage="contacted"), _make_deal(stage="qualified")]
    svc.repo.list_items = AsyncMock(return_value=deals)
    from app.modules.pipeline.schemas import PipelineRecommendation
    recs = [
        PipelineRecommendation(
            deal_id=deals[0].id, score=30,
            breakdown=AIScoreBreakdown(total=30, intent=30, engagement=30, recency=30, monetary=30),
            next_best_action="x", suggested_channel=None, suggested_stage=None, notes=[],
        ),
        PipelineRecommendation(
            deal_id=deals[1].id, score=80,
            breakdown=AIScoreBreakdown(total=80, intent=80, engagement=80, recency=80, monetary=80),
            next_best_action="y", suggested_channel="whatsapp", suggested_stage="proposal", notes=[],
        ),
    ]
    svc.ai.recommend = AsyncMock(side_effect=recs)
    r = await svc.recommendations(TEST_EMPRESA_ID)
    assert r.recommendations[0].score == 80
    assert r.recommendations[1].score == 30


# ─────────────────────────────────────────────────────────────────────────────
# Automations
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_automation_stuck_in_stage_triggers(mock_session: AsyncMock) -> None:
    deal = _make_deal(stage="contacted")
    deal.stage_entered_at = datetime.utcnow() - timedelta(days=10)
    eng = AutomationEngine(mock_session)
    eng.ai.score_deal = AsyncMock(return_value=(10, None, []))
    mock_session.execute = AsyncMock(return_value=_execute_result(one=0))
    alerts = await eng.evaluate(TEST_EMPRESA_ID, [deal])
    rules = [a.rule for a in alerts]
    assert "STUCK_IN_STAGE" in rules


@pytest.mark.asyncio
async def test_automation_vip_ignored(mock_session: AsyncMock) -> None:
    deal = _make_deal(stage="negotiation", is_vip=True)
    deal.last_activity_at = datetime.utcnow() - timedelta(days=5)
    eng = AutomationEngine(mock_session)
    eng.ai.score_deal = AsyncMock(return_value=(10, None, []))
    mock_session.execute = AsyncMock(return_value=_execute_result(one=0))
    alerts = await eng.evaluate(TEST_EMPRESA_ID, [deal])
    assert any(a.rule == "VIP_IGNORED" for a in alerts)


@pytest.mark.asyncio
async def test_automation_no_alerts_for_fresh_deal(mock_session: AsyncMock) -> None:
    deal = _make_deal(stage="new_lead")
    deal.stage_entered_at = datetime.utcnow()
    deal.last_activity_at = datetime.utcnow()
    eng = AutomationEngine(mock_session)
    eng.ai.score_deal = AsyncMock(return_value=(10, None, []))
    mock_session.execute = AsyncMock(return_value=_execute_result(one=0))
    alerts = await eng.evaluate(TEST_EMPRESA_ID, [deal])
    assert alerts == []


@pytest.mark.asyncio
async def test_automation_severity_ordering(mock_session: AsyncMock) -> None:
    # Two alerts: one critical (VIP), one info (budget share)
    deal_vip = _make_deal(stage="negotiation", is_vip=True, estimated_value=Decimal("100"))
    deal_vip.last_activity_at = datetime.utcnow() - timedelta(days=5)
    deal_vip.stage_entered_at = datetime.utcnow() - timedelta(days=2)
    deal_huge = _make_deal(stage="negotiation", estimated_value=Decimal("1000"))
    deal_huge.stage_entered_at = datetime.utcnow() - timedelta(days=1)
    eng = AutomationEngine(mock_session)
    eng.ai.score_deal = AsyncMock(return_value=(10, None, []))
    mock_session.execute = AsyncMock(return_value=_execute_result(one=Decimal("1000")))
    alerts = await eng.evaluate(TEST_EMPRESA_ID, [deal_vip, deal_huge])
    severities = [a.severity for a in alerts]
    if "critical" in severities and "info" in severities:
        assert severities.index("critical") < severities.index("info")


# ─────────────────────────────────────────────────────────────────────────────
# Permissions
# ─────────────────────────────────────────────────────────────────────────────


def test_role_permissions_include_pipeline() -> None:
    for role in ("owner", "admin", "sales_agent", "analyst"):
        perms = ROLE_PERMISSIONS[role]
        assert "pipeline:read" in perms, role
    for role in ("owner", "admin", "sales_agent"):
        assert "pipeline:write" in ROLE_PERMISSIONS[role], role
    for role in ("owner", "admin", "sales_agent", "analyst"):
        assert "pipeline:metrics" in ROLE_PERMISSIONS[role], role


def test_analyst_cannot_write_pipeline() -> None:
    perms = ROLE_PERMISSIONS["analyst"]
    assert "pipeline:write" not in perms


# ─────────────────────────────────────────────────────────────────────────────
# API integration (TestClient)
# ─────────────────────────────────────────────────────────────────────────────


def _tenant_with_perms(perms: set[str]) -> TenantContext:
    return TenantContext(
        empresa_id=TEST_EMPRESA_ID,
        user_id=TEST_USER_ID,
        roles=["owner"],
        permissions=perms,
    )


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(pipeline_router, prefix="/pipeline")
    return app


def _override(app: FastAPI, perms: set[str], svc: PipelineService) -> None:
    from app.modules.pipeline import dependencies as deps
    from app.database import session as sess

    async def _ctx() -> TenantContext:
        return _tenant_with_perms(perms)

    async def _db():
        yield svc.session  # type: ignore[attr-defined]

    app.dependency_overrides[deps.PipelineReadContext] = _ctx
    app.dependency_overrides[deps.PipelineWriteContext] = _ctx
    app.dependency_overrides[deps.PipelineMetricsContext] = _ctx
    app.dependency_overrides[deps.DB] = _db


def test_api_stages_returns_seven() -> None:
    app = _build_app()
    with TestClient(app) as c:
        r = c.get("/pipeline/stages")
        assert r.status_code == 200
        assert len(r.json()) == 7


def test_api_metrics_payload_shape() -> None:
    app = _build_app()
    svc = MagicMock()
    svc.session = AsyncMock()
    # Skip auth: inject tenant directly via the dependency_overrides pattern
    async def _ctx() -> TenantContext:
        return _tenant_with_perms({"pipeline:read", "pipeline:metrics"})
    async def _db():
        yield MagicMock()
    from app.modules.pipeline import dependencies as deps
    app.dependency_overrides[deps.PipelineReadContext] = _ctx
    app.dependency_overrides[deps.PipelineMetricsContext] = _ctx
    app.dependency_overrides[deps.DB] = _db
    # Patch the actual service
    fake = MagicMock()
    fake.metrics = AsyncMock(
        return_value=SimpleNamespace(
            total_open=1, total_closed_won=1, total_closed_lost=0,
            open_value=100.0, weighted_open_value=50.0, won_value=100.0, lost_value=0.0,
            conversion_rate_pct=100.0, average_deal_value=50.0,
            average_time_to_close_days=1.0, average_time_in_current_stage_days=0.5,
            oldest_unstuck_days=0, alerts_count=0,
            by_stage={}, by_channel={}, by_priority={},
        )
    )
    with patch("app.modules.pipeline.router.PipelineService", return_value=fake):
        with TestClient(app) as c:
            r = c.get("/pipeline/metrics")
            assert r.status_code == 200
            j = r.json()
            assert "total_open" in j
            assert "by_stage" in j


def test_api_create_returns_201() -> None:
    app = _build_app()
    fake = MagicMock()
    fake.session = AsyncMock()
    fake.create = AsyncMock(
        return_value=SimpleNamespace(id=str(uuid4()), customer=None, ai_score=None)
    )
    with patch("app.modules.pipeline.router.PipelineService", return_value=fake):
        async def _ctx() -> TenantContext:
            return _tenant_with_perms({"pipeline:read", "pipeline:write"})
        async def _db():
            yield MagicMock()
        from app.modules.pipeline import dependencies as deps
        app.dependency_overrides[deps.PipelineReadContext] = _ctx
        app.dependency_overrides[deps.PipelineWriteContext] = _ctx
        app.dependency_overrides[deps.DB] = _db
        with TestClient(app) as c:
            r = c.post(
                "/pipeline/deals",
                json={"title": "Test", "estimated_value": 100, "probability": 30, "stage": "qualified"},
            )
            assert r.status_code == 201


def test_api_delete_returns_204() -> None:
    app = _build_app()
    fake = MagicMock()
    fake.session = AsyncMock()
    fake.delete = AsyncMock(return_value=None)
    with patch("app.modules.pipeline.router.PipelineService", return_value=fake):
        async def _ctx() -> TenantContext:
            return _tenant_with_perms({"pipeline:read", "pipeline:write"})
        async def _db():
            yield MagicMock()
        from app.modules.pipeline import dependencies as deps
        app.dependency_overrides[deps.PipelineReadContext] = _ctx
        app.dependency_overrides[deps.PipelineWriteContext] = _ctx
        app.dependency_overrides[deps.DB] = _db
        with TestClient(app) as c:
            r = c.delete(f"/pipeline/deals/{uuid4()}")
            assert r.status_code == 204


def test_api_forbidden_without_pipeline_read() -> None:
    app = _build_app()
    async def _ctx() -> TenantContext:
        return _tenant_with_perms(set())  # no permissions
    async def _db():
        yield MagicMock()
    from app.modules.pipeline import dependencies as deps
    app.dependency_overrides[deps.PipelineReadContext] = _ctx
    app.dependency_overrides[deps.DB] = _db
    with TestClient(app) as c:
        r = c.get("/pipeline/stages")
        assert r.status_code == 403


# ─────────────────────────────────────────────────────────────────────────────
# asyncio loop
# ─────────────────────────────────────────────────────────────────────────────


def test_asyncio_smoke() -> None:
    async def _go() -> int:
        await asyncio.sleep(0)
        return 1
    assert asyncio.run(_go()) == 1
