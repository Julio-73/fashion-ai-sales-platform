"""Unit tests for the AutomationRuleEngine — uses a mock AsyncSession
so we never touch a real database."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
import pytest_asyncio

from app.modules.automation.engine import (
    LEAD_IDLE_24H_HOURS,
    LEAD_IDLE_48H_HOURS,
    NEGOTIATION_STUCK_DAYS,
    VIP_INACTIVE_DAYS,
    AutomationRuleEngine,
)
from app.modules.automation.models import (
    RULE_001,
    RULE_002,
    RULE_003,
    RULE_004,
    RULE_005,
    RULE_006,
    RULE_007,
    AutomationRule,
)


EMPRESA_ID = UUID("11111111-1111-4111-8111-111111111111")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _now() -> datetime:
    return datetime(2026, 6, 7, 12, 0, 0, tzinfo=timezone.utc)


def _rule(rule_key: str) -> AutomationRule:
    r = MagicMock(spec=AutomationRule)
    r.id = uuid4()
    r.empresa_id = EMPRESA_ID
    r.rule_key = rule_key
    r.name = rule_key
    r.description = ""
    r.trigger_type = "x"
    r.enabled = True
    r.config = {}
    return r


def _build_engine(rules_by_key: dict[str, AutomationRule]) -> tuple[AutomationRuleEngine, AsyncMock]:
    session = AsyncMock()
    session.commit = AsyncMock()
    session.execute = AsyncMock()
    session.flush = AsyncMock()

    engine = AutomationRuleEngine(session)
    engine.rules = MagicMock()
    engine.rules.list_rules = AsyncMock(
        return_value=list(rules_by_key.values())
    )
    engine.rules.upsert_seed = AsyncMock(
        side_effect=lambda **kw: _rule(kw["rule_key"])
    )
    engine.tasks = MagicMock()
    engine.events = MagicMock()
    engine.tasks.mark_overdue = AsyncMock()
    engine.tasks.find_open_duplicate = AsyncMock(return_value=None)
    engine.tasks.create = AsyncMock(
        side_effect=lambda **kw: SimpleNamespace(id=uuid4(), **kw)
    )
    engine.tasks.update = AsyncMock(
        side_effect=lambda *, task, changes: SimpleNamespace(**{**task.__dict__, **changes})
    )
    engine.events.create = AsyncMock(
        side_effect=lambda **kw: SimpleNamespace(id=uuid4(), **kw)
    )
    return engine, session


def _scalar_result(rows: list) -> MagicMock:
    """Build a MagicMock that mimics the SQLAlchemy ``Result`` API for
    ``scalars()`` and ``all()``."""
    result = MagicMock()
    scalars = MagicMock()
    scalars.all = MagicMock(return_value=rows)
    scalars.__iter__ = MagicMock(return_value=iter(rows))
    result.scalars = MagicMock(return_value=scalars)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Seeding
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_engine_ensure_default_rules_seeds_seven() -> None:
    engine, _ = _build_engine({})
    engine.rules.upsert_seed = AsyncMock(
        side_effect=lambda **kw: _rule(kw["rule_key"])
    )
    rules = await engine.ensure_default_rules(EMPRESA_ID)
    assert len(rules) == 7
    keys = {r.rule_key for r in rules}
    assert keys == {RULE_001, RULE_002, RULE_003, RULE_004, RULE_005, RULE_006, RULE_007}


# ─────────────────────────────────────────────────────────────────────────────
# mark_overdue
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_engine_runs_mark_overdue_on_every_cycle() -> None:
    engine, session = _build_engine({_k: _rule(_k) for _k in (RULE_001,)})
    # No DB rows: scalars should be empty
    session.execute = AsyncMock(return_value=_scalar_result([]))
    stats = await engine.run(EMPRESA_ID, now=_now())
    engine.tasks.mark_overdue.assert_awaited_once()
    assert stats.tasks_created == 0
    assert stats.events_created == 0


# ─────────────────────────────────────────────────────────────────────────────
# RULE 001 — LEAD_NO_RESPONSE_24H
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_rule_001_creates_task_for_idle_lead() -> None:
    cust = SimpleNamespace(
        id=uuid4(),
        full_name="Test Lead",
        lead_status="new",
        last_interaction_at=_now() - timedelta(hours=30),
        last_conversation_id=None,
        lead_score=10,
        priority="cold",
    )
    engine, session = _build_engine({RULE_001: _rule(RULE_001)})
    session.execute = AsyncMock(return_value=_scalar_result([cust]))
    stats = await engine.run(EMPRESA_ID, now=_now())
    assert stats.tasks_created == 1
    assert stats.events_created == 0
    engine.tasks.create.assert_awaited()


@pytest.mark.asyncio
async def test_rule_001_skips_24h_or_less() -> None:
    cust = SimpleNamespace(
        id=uuid4(),
        full_name="X",
        lead_status="new",
        last_interaction_at=_now() - timedelta(hours=2),
        last_conversation_id=None,
        lead_score=10,
        priority="cold",
    )
    engine, session = _build_engine({RULE_001: _rule(RULE_001)})
    session.execute = AsyncMock(return_value=_scalar_result([cust]))
    stats = await engine.run(EMPRESA_ID, now=_now())
    assert stats.tasks_created == 0


# ─────────────────────────────────────────────────────────────────────────────
# RULE 002 — LEAD_NO_RESPONSE_48H
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_rule_002_creates_task_and_event() -> None:
    cust = SimpleNamespace(
        id=uuid4(),
        full_name="Silent Lead",
        lead_status="negotiating",
        last_interaction_at=_now() - timedelta(hours=72),
        last_conversation_id=None,
        lead_score=30,
        priority="cold",
    )
    engine, session = _build_engine({RULE_002: _rule(RULE_002)})
    session.execute = AsyncMock(return_value=_scalar_result([cust]))
    stats = await engine.run(EMPRESA_ID, now=_now())
    assert stats.tasks_created == 1
    assert stats.events_created == 1
    engine.events.create.assert_awaited()


@pytest.mark.asyncio
async def test_rule_002_skips_fresh_leads() -> None:
    cust = SimpleNamespace(
        id=uuid4(),
        full_name="Fresh",
        lead_status="new",
        last_interaction_at=_now() - timedelta(hours=2),
        last_conversation_id=None,
        lead_score=10,
        priority="cold",
    )
    engine, session = _build_engine({RULE_002: _rule(RULE_002)})
    session.execute = AsyncMock(return_value=_scalar_result([cust]))
    stats = await engine.run(EMPRESA_ID, now=_now())
    assert stats.tasks_created == 0


# ─────────────────────────────────────────────────────────────────────────────
# RULE 003 — NEGOTIATION_STUCK_7D
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_rule_003_creates_task_for_stuck_negotiation() -> None:
    deal = SimpleNamespace(
        id=uuid4(),
        title="Acme deal",
        stage="negotiation",
        stage_entered_at=_now() - timedelta(days=10),
        last_activity_at=_now() - timedelta(days=10),
        estimated_value=Decimal("1000"),
        customer_id=uuid4(),
        conversation_id=None,
        is_vip=False,
        won_reason=None,
        lost_reason=None,
    )
    engine, session = _build_engine({RULE_003: _rule(RULE_003)})
    # First call: deals; second call: customer map → empty
    session.execute = AsyncMock(side_effect=[_scalar_result([deal]), _scalar_result([])])
    stats = await engine.run(EMPRESA_ID, now=_now())
    assert stats.tasks_created == 1
    assert stats.events_created == 1


@pytest.mark.asyncio
async def test_rule_003_skips_recent_negotiation() -> None:
    engine, session = _build_engine({RULE_003: _rule(RULE_003)})
    session.execute = AsyncMock(return_value=_scalar_result([]))
    stats = await engine.run(EMPRESA_ID, now=_now())
    assert stats.tasks_created == 0


# ─────────────────────────────────────────────────────────────────────────────
# RULE 004 — VIP_CUSTOMER_INACTIVE_30D
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_rule_004_creates_recovery_task() -> None:
    cust = SimpleNamespace(
        id=uuid4(),
        full_name="VIP Lead",
        lead_status="interested",
        last_interaction_at=_now() - timedelta(days=40),
        last_conversation_id=None,
        lead_score=90,
        priority="hot",
    )
    engine, session = _build_engine({RULE_004: _rule(RULE_004)})
    session.execute = AsyncMock(return_value=_scalar_result([cust]))
    stats = await engine.run(EMPRESA_ID, now=_now())
    assert stats.tasks_created == 1
    assert stats.events_created == 1


# ─────────────────────────────────────────────────────────────────────────────
# RULE 005 — NEW_HIGH_VALUE_LEAD
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_rule_005_emits_alert_for_high_value_deal() -> None:
    deal = SimpleNamespace(
        id=uuid4(),
        title="Big Deal",
        stage="qualified",
        stage_entered_at=_now() - timedelta(hours=2),
        last_activity_at=_now() - timedelta(hours=2),
        estimated_value=Decimal("5000"),
        customer_id=uuid4(),
        conversation_id=None,
        is_vip=False,
        won_reason=None,
        lost_reason=None,
    )
    engine, session = _build_engine({RULE_005: _rule(RULE_005)})
    # First call: deals; second call: customer map (empty)
    session.execute = AsyncMock(side_effect=[_scalar_result([deal]), _scalar_result([])])
    stats = await engine.run(EMPRESA_ID, now=_now())
    assert stats.tasks_created == 1
    assert stats.events_created == 1


@pytest.mark.asyncio
async def test_rule_005_skips_low_value_deals() -> None:
    deal = SimpleNamespace(
        id=uuid4(),
        title="Tiny Deal",
        stage="contacted",
        stage_entered_at=_now(),
        last_activity_at=_now(),
        estimated_value=Decimal("50"),
        customer_id=uuid4(),
        conversation_id=None,
        is_vip=False,
        won_reason=None,
        lost_reason=None,
    )
    engine, session = _build_engine({RULE_005: _rule(RULE_005)})
    session.execute = AsyncMock(side_effect=[_scalar_result([deal]), _scalar_result([])])
    stats = await engine.run(EMPRESA_ID, now=_now())
    assert stats.tasks_created == 0
    assert stats.events_created == 0


# ─────────────────────────────────────────────────────────────────────────────
# RULE 006 — PIPELINE_WON
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_rule_006_emits_event_for_won_deal() -> None:
    deal = SimpleNamespace(
        id=uuid4(),
        title="Closed Won",
        stage="won",
        stage_entered_at=_now() - timedelta(hours=1),
        last_activity_at=_now() - timedelta(hours=1),
        estimated_value=Decimal("1500"),
        customer_id=uuid4(),
        conversation_id=None,
        is_vip=False,
        won_reason="Best price",
        lost_reason=None,
    )
    engine, session = _build_engine({RULE_006: _rule(RULE_006)})
    session.execute = AsyncMock(return_value=_scalar_result([deal]))
    stats = await engine.run(EMPRESA_ID, now=_now())
    assert stats.tasks_created == 1
    assert stats.events_created == 1


# ─────────────────────────────────────────────────────────────────────────────
# RULE 007 — PIPELINE_LOST
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_rule_007_emits_event_for_lost_deal() -> None:
    deal = SimpleNamespace(
        id=uuid4(),
        title="Closed Lost",
        stage="lost",
        stage_entered_at=_now() - timedelta(hours=1),
        last_activity_at=_now() - timedelta(hours=1),
        estimated_value=Decimal("800"),
        customer_id=uuid4(),
        conversation_id=None,
        is_vip=False,
        won_reason=None,
        lost_reason="Price too high",
    )
    engine, session = _build_engine({RULE_007: _rule(RULE_007)})
    session.execute = AsyncMock(return_value=_scalar_result([deal]))
    stats = await engine.run(EMPRESA_ID, now=_now())
    assert stats.tasks_created == 1
    assert stats.events_created == 1


# ─────────────────────────────────────────────────────────────────────────────
# Idempotency
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_engine_skips_task_when_duplicate_open_exists() -> None:
    cust = SimpleNamespace(
        id=uuid4(),
        full_name="X",
        lead_status="new",
        last_interaction_at=_now() - timedelta(hours=30),
        last_conversation_id=None,
        lead_score=10,
        priority="cold",
    )
    engine, session = _build_engine({RULE_001: _rule(RULE_001)})
    # Inject a duplicate
    dup = SimpleNamespace(id=uuid4(), priority="medium")
    engine.tasks.find_open_duplicate = AsyncMock(return_value=dup)
    session.execute = AsyncMock(return_value=_scalar_result([cust]))
    stats = await engine.run(EMPRESA_ID, now=_now())
    assert stats.tasks_created == 0
    engine.tasks.create.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# Disabled / unknown rules
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_engine_skips_disabled_rules() -> None:
    engine, session = _build_engine({})  # no enabled rules at all
    session.execute = AsyncMock(return_value=_scalar_result([]))
    stats = await engine.run(EMPRESA_ID, now=_now())
    assert stats.rules_skipped == (
        RULE_001, RULE_002, RULE_003, RULE_004, RULE_005, RULE_006, RULE_007,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Constants — sanity
# ─────────────────────────────────────────────────────────────────────────────
def test_thresholds_sane() -> None:
    assert LEAD_IDLE_24H_HOURS == 24
    assert LEAD_IDLE_48H_HOURS == 48
    assert NEGOTIATION_STUCK_DAYS == 7
    assert VIP_INACTIVE_DAYS == 30
