"""Unit tests for the Automation Engine — models, schemas, and the
pure (no I/O) AutomationAIService."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.modules.automation.ai import (
    ACTION_CALL,
    ACTION_DISCOUNT,
    ACTION_ESCALATE,
    ACTION_FOLLOW_UP,
    ACTION_LOSS_LOG,
    ACTION_PROPOSAL,
    ACTION_RECOVERY,
    ACTION_WIN_LOG,
    AutomationAIService,
)
from app.modules.automation.models import (
    DEFAULT_RULES,
    ENTITY_TYPE_VALUES,
    EVENT_SEVERITY_VALUES,
    RULE_001,
    RULE_002,
    RULE_003,
    RULE_004,
    RULE_005,
    RULE_006,
    RULE_007,
    TASK_PRIORITY_VALUES,
    TASK_STATUS_VALUES,
    TASK_TYPE_VALUES,
    AutomationEvent,
    AutomationRule,
    AutomationTask,
)
from app.modules.automation.schemas import (
    AutomationRuleCreate,
    AutomationRuleUpdate,
    AutomationTaskCreate,
    AutomationTaskUpdate,
)


# ─────────────────────────────────────────────────────────────────────────────
# Models — constants & defaults
# ─────────────────────────────────────────────────────────────────────────────
def test_task_status_values_complete() -> None:
    assert set(TASK_STATUS_VALUES) == {
        "pending",
        "in_progress",
        "completed",
        "cancelled",
        "overdue",
    }


def test_task_priority_values_complete() -> None:
    assert set(TASK_PRIORITY_VALUES) == {"low", "medium", "high", "critical"}


def test_task_type_values_complete() -> None:
    expected = {
        "follow_up",
        "call",
        "proposal",
        "meeting",
        "recovery",
        "alert",
        "win_log",
        "loss_log",
        "pipeline_event",
        "inventory_check",
        "order_risk",
    }
    assert set(TASK_TYPE_VALUES) == expected


def test_event_severity_values() -> None:
    assert set(EVENT_SEVERITY_VALUES) == {"info", "warning", "critical"}


def test_entity_type_values() -> None:
    assert set(ENTITY_TYPE_VALUES) == {
        "customer",
        "pipeline_item",
        "conversation",
        "order",
        "inventory_item",
        "none",
    }


def test_default_rules_seeded() -> None:
    keys = {r["rule_key"] for r in DEFAULT_RULES}
    assert keys == {RULE_001, RULE_002, RULE_003, RULE_004, RULE_005, RULE_006, RULE_007}


def test_default_rules_have_required_fields() -> None:
    for r in DEFAULT_RULES:
        assert r["name"]
        assert r["trigger_type"]
        assert r["task_type"] in TASK_TYPE_VALUES
        assert r["default_priority"] in TASK_PRIORITY_VALUES
        assert r["default_severity"] in EVENT_SEVERITY_VALUES


# ─────────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────────
def test_rule_create_schema_ok() -> None:
    payload = AutomationRuleCreate(
        rule_key="MY_RULE",
        name="Custom rule",
        trigger_type="customer_idle",
        config={"foo": "bar"},
    )
    assert payload.enabled is True
    assert payload.config == {"foo": "bar"}


def test_rule_create_schema_rejects_short_name() -> None:
    with pytest.raises(ValidationError):
        AutomationRuleCreate(rule_key="X", name="a", trigger_type="customer_idle")


def test_rule_update_partial() -> None:
    payload = AutomationRuleUpdate(enabled=False)
    data = payload.model_dump(exclude_unset=True)
    assert data == {"enabled": False}


def test_task_create_with_optional_ids() -> None:
    cust = uuid4()
    deal = uuid4()
    payload = AutomationTaskCreate(
        title="Llamar al cliente",
        customer_id=cust,
        pipeline_item_id=deal,
    )
    assert payload.priority == "medium"
    assert payload.task_type == "follow_up"
    assert payload.status == "pending"


def test_task_update_partial() -> None:
    payload = AutomationTaskUpdate(status="completed", priority="low")
    data = payload.model_dump(exclude_unset=True)
    assert data == {"status": "completed", "priority": "low"}


def test_task_create_rejects_invalid_status() -> None:
    with pytest.raises(ValidationError):
        AutomationTaskCreate(title="X", status="bogus")  # type: ignore[arg-type]


def test_task_create_ai_score_bounds() -> None:
    with pytest.raises(ValidationError):
        AutomationTaskCreate(title="X", ai_score=150)
    with pytest.raises(ValidationError):
        AutomationTaskCreate(title="X", ai_score=-1)


# ─────────────────────────────────────────────────────────────────────────────
# AutomationAIService — pure
# ─────────────────────────────────────────────────────────────────────────────
def _now() -> datetime:
    return datetime(2026, 6, 7, 12, 0, 0, tzinfo=timezone.utc)


def test_ai_priority_rule_001_recent_returns_medium() -> None:
    ai = AutomationAIService()
    cust = SimpleNamespace(
        last_interaction_at=_now() - timedelta(hours=25),
        lead_score=30,
    )
    prio, _, action, score = ai.recommend(
        RULE_001, customer=cust, deal=None, now=_now()
    )
    assert prio in {"medium", "high"}
    assert action == ACTION_FOLLOW_UP
    assert 0 <= score <= 100


def test_ai_priority_rule_002_48h_critical() -> None:
    ai = AutomationAIService()
    cust = SimpleNamespace(
        last_interaction_at=_now() - timedelta(hours=72),
        lead_score=10,
    )
    prio, reason, action, _ = ai.recommend(
        RULE_002, customer=cust, deal=None, now=_now()
    )
    assert prio == "critical"
    assert action == ACTION_CALL
    assert "72" in reason or "silencio" in reason


def test_ai_priority_rule_002_with_high_lead_score() -> None:
    ai = AutomationAIService()
    cust = SimpleNamespace(
        last_interaction_at=_now() - timedelta(hours=50),
        lead_score=85,
    )
    _, _, _, score = ai.recommend(
        RULE_002, customer=cust, deal=None, now=_now()
    )
    # Score should incorporate the lead_score bonus
    assert score >= 75


def test_ai_priority_rule_003_negotiation_stuck_escalate() -> None:
    ai = AutomationAIService()
    deal = SimpleNamespace(
        stage="negotiation",
        stage_entered_at=_now() - timedelta(days=15),
        last_activity_at=_now(),
        estimated_value=Decimal("1000"),
        is_vip=False,
    )
    _, _, action, _ = ai.recommend(
        RULE_003, customer=None, deal=deal, now=_now()
    )
    assert action == ACTION_ESCALATE


def test_ai_priority_rule_004_vip_critical() -> None:
    ai = AutomationAIService()
    cust = SimpleNamespace(
        last_interaction_at=_now() - timedelta(days=40),
        lead_score=85,
    )
    deal = SimpleNamespace(is_vip=True, estimated_value=Decimal("0"), stage="won", stage_entered_at=_now(), last_activity_at=_now())
    prio, _, action, _ = ai.recommend(
        RULE_004, customer=cust, deal=deal, now=_now()
    )
    assert prio == "critical"
    assert action == ACTION_RECOVERY


def test_ai_priority_rule_005_low_value_low_score() -> None:
    ai = AutomationAIService()
    deal = SimpleNamespace(
        stage="contacted",
        stage_entered_at=_now(),
        last_activity_at=_now(),
        estimated_value=Decimal("100"),
        is_vip=False,
    )
    cust = SimpleNamespace(lead_score=10, last_interaction_at=None)
    _, _, _, score = ai.recommend(
        RULE_005, customer=cust, deal=deal, now=_now()
    )
    # Low value + low score → low AI score (< 60 means the engine
    # will skip emitting a task)
    assert score < 60


def test_ai_priority_rule_005_high_value_escalate() -> None:
    ai = AutomationAIService()
    deal = SimpleNamespace(
        stage="qualified",
        stage_entered_at=_now(),
        last_activity_at=_now(),
        estimated_value=Decimal("5000"),
        is_vip=False,
    )
    cust = SimpleNamespace(lead_score=70, last_interaction_at=None)
    _, _, action, score = ai.recommend(
        RULE_005, customer=cust, deal=deal, now=_now()
    )
    assert action == ACTION_ESCALATE
    assert score >= 60


def test_ai_priority_rule_006_win_log_low() -> None:
    ai = AutomationAIService()
    deal = SimpleNamespace(
        stage="won",
        stage_entered_at=_now(),
        last_activity_at=_now(),
        estimated_value=Decimal("1000"),
        is_vip=False,
    )
    prio, _, action, _ = ai.recommend(
        RULE_006, customer=None, deal=deal, now=_now()
    )
    assert prio == "low"
    assert action == ACTION_WIN_LOG


def test_ai_priority_rule_007_loss_log_medium() -> None:
    ai = AutomationAIService()
    deal = SimpleNamespace(
        stage="lost",
        stage_entered_at=_now() - timedelta(days=10),
        last_activity_at=_now(),
        estimated_value=Decimal("500"),
        is_vip=False,
    )
    prio, _, action, _ = ai.recommend(
        RULE_007, customer=None, deal=deal, now=_now()
    )
    assert prio == "medium"
    assert action == ACTION_LOSS_LOG


def test_ai_score_is_clamped_0_100() -> None:
    ai = AutomationAIService()
    cust = SimpleNamespace(
        last_interaction_at=_now() - timedelta(days=400),
        lead_score=200,
    )
    _, _, _, score = ai.recommend(
        RULE_002, customer=cust, deal=None, now=_now()
    )
    assert 0 <= score <= 100


def test_ai_handles_missing_customer() -> None:
    ai = AutomationAIService()
    prio, reason, action, score = ai.recommend(
        RULE_001, customer=None, deal=None, now=_now()
    )
    assert prio in TASK_PRIORITY_VALUES
    assert score >= 0
    assert action in {
        ACTION_FOLLOW_UP,
        ACTION_CALL,
        ACTION_PROPOSAL,
        ACTION_RECOVERY,
        ACTION_DISCOUNT,
        ACTION_ESCALATE,
        ACTION_WIN_LOG,
        ACTION_LOSS_LOG,
    }


def test_ai_default_priority_for_unknown_rule() -> None:
    ai = AutomationAIService()
    prio, _, action, _ = ai.recommend(
        "UNKNOWN_RULE", customer=None, deal=None, now=_now()
    )
    assert prio == "medium"


# ─────────────────────────────────────────────────────────────────────────────
# ORM models — to_dict / repr sanity (no DB)
# ─────────────────────────────────────────────────────────────────────────────
def test_automation_rule_repr_contains_key() -> None:
    rule = AutomationRule(
        empresa_id=UUID("11111111-1111-4111-8111-111111111111"),
        rule_key="X",
        name="X",
        trigger_type="customer_idle",
    )
    text = repr(rule)
    assert "AutomationRule" in text


def test_automation_task_repr_contains_type() -> None:
    task = AutomationTask(
        empresa_id=UUID("11111111-1111-4111-8111-111111111111"),
        title="t",
        task_type="follow_up",
        priority="medium",
        status="pending",
    )
    text = repr(task)
    assert "AutomationTask" in text


def test_automation_event_repr_contains_key() -> None:
    ev = AutomationEvent(
        empresa_id=UUID("11111111-1111-4111-8111-111111111111"),
        rule_key="LEAD_NO_RESPONSE_24H",
        event_type="lead_idle",
        entity_type="customer",
    )
    text = repr(ev)
    assert "AutomationEvent" in text
