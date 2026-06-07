"""Integration tests for the automation router."""
from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.security.dependencies import TenantContext
from app.core.security.permissions import ROLE_PERMISSIONS
from app.modules.automation.router import router as automation_router


EMPRESA_ID = UUID("11111111-1111-4111-8111-111111111111")
USER_ID = UUID("22222222-2222-4222-8222-222222222222")


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────
def _tenant() -> TenantContext:
    return TenantContext(
        empresa_id=EMPRESA_ID,
        user_id=USER_ID,
        roles=["owner"],
        permissions=set(ROLE_PERMISSIONS["owner"]),
    )


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(automation_router, prefix="/automation")
    return TestClient(app)


@pytest.fixture
def auth_override(client: TestClient):
    """Override the security dependency to inject a tenant context."""
    from app.modules.automation.dependencies import (
        automation_read_dep,
        automation_write_dep,
    )

    async def _read() -> TenantContext:
        return _tenant()

    async def _write() -> TenantContext:
        return _tenant()

    app = client.app
    app.dependency_overrides[automation_read_dep] = _read
    app.dependency_overrides[automation_write_dep] = _write
    yield app
    app.dependency_overrides.clear()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _rule(rule_key: str = "LEAD_NO_RESPONSE_24H", enabled: bool = True):
    r = SimpleNamespace(
        id=uuid4(),
        empresa_id=EMPRESA_ID,
        rule_key=rule_key,
        name=rule_key,
        description=None,
        trigger_type="customer_idle",
        enabled=enabled,
        config={},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    return r


def _task(
    *,
    status: str = "pending",
    priority: str = "medium",
    task_type: str = "follow_up",
    due_date=None,
    title: str = "Tarea de prueba",
):
    return SimpleNamespace(
        id=uuid4(),
        empresa_id=EMPRESA_ID,
        rule_id=None,
        customer_id=None,
        pipeline_item_id=None,
        conversation_id=None,
        title=title,
        description=None,
        task_type=task_type,
        priority=priority,
        status=status,
        ai_reason=None,
        ai_next_action=None,
        ai_score=None,
        due_date=due_date,
        completed_at=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Rules endpoints
# ─────────────────────────────────────────────────────────────────────────────
def test_list_rules_returns_ok(client: TestClient, auth_override) -> None:
    with patch("app.modules.automation.router.AutomationService") as Svc:
        svc_instance = MagicMock()
        svc_instance.list_rules = AsyncMock(return_value=[_rule()])
        Svc.return_value = svc_instance
        # Bypass the DB dep
        from app.modules.automation.dependencies import get_db_session
        async def _db():
            yield MagicMock()
        client.app.dependency_overrides[get_db_session] = _db
        resp = client.get("/automation/rules")
        assert resp.status_code == 200
        assert resp.json()[0]["rule_key"] == "LEAD_NO_RESPONSE_24H"


def test_seed_rules_invokes_service(client: TestClient, auth_override) -> None:
    with patch("app.modules.automation.router.AutomationService") as Svc:
        svc_instance = MagicMock()
        svc_instance.ensure_seeded = AsyncMock(return_value=[_rule()])
        Svc.return_value = svc_instance
        from app.modules.automation.dependencies import get_db_session
        async def _db():
            yield MagicMock()
        client.app.dependency_overrides[get_db_session] = _db
        resp = client.post("/automation/rules/seed")
        assert resp.status_code == 200
        svc_instance.ensure_seeded.assert_awaited()


def test_patch_rule_returns_ok(client: TestClient, auth_override) -> None:
    rule = _rule(enabled=False)
    with patch("app.modules.automation.router.AutomationService") as Svc:
        svc_instance = MagicMock()
        svc_instance.update_rule = AsyncMock(return_value=rule)
        Svc.return_value = svc_instance
        from app.modules.automation.dependencies import get_db_session
        async def _db():
            yield MagicMock()
        client.app.dependency_overrides[get_db_session] = _db
        resp = client.patch(f"/automation/rules/{rule.id}", json={"enabled": False})
        assert resp.status_code == 200
        assert resp.json()["enabled"] is False


# ─────────────────────────────────────────────────────────────────────────────
# Engine
# ─────────────────────────────────────────────────────────────────────────────
def test_run_engine_returns_stats(client: TestClient, auth_override) -> None:
    with patch("app.modules.automation.router.AutomationService") as Svc:
        svc_instance = MagicMock()
        svc_instance.run_engine = AsyncMock(return_value=SimpleNamespace(
            scanned_customers=1, scanned_deals=2, scanned_orders=0, scanned_inventory=0,
            tasks_created=3, tasks_updated=0, events_created=4, rules_skipped=()
        ))
        Svc.return_value = svc_instance
        from app.modules.automation.dependencies import get_db_session
        async def _db():
            yield MagicMock()
        client.app.dependency_overrides[get_db_session] = _db
        resp = client.post("/automation/run")
        assert resp.status_code == 200
        body = resp.json()
        assert body["tasks_created"] == 3
        assert body["events_created"] == 4


# ─────────────────────────────────────────────────────────────────────────────
# Tasks endpoints
# ─────────────────────────────────────────────────────────────────────────────
def test_list_tasks_returns_ok(client: TestClient, auth_override) -> None:
    with patch("app.modules.automation.router.AutomationService") as Svc:
        svc_instance = MagicMock()
        svc_instance.list_tasks = AsyncMock(return_value=[_task()])
        Svc.return_value = svc_instance
        from app.modules.automation.dependencies import get_db_session
        async def _db():
            yield MagicMock()
        client.app.dependency_overrides[get_db_session] = _db
        resp = client.get("/automation/tasks?status=pending")
        assert resp.status_code == 200
        assert resp.json()[0]["status"] == "pending"


def test_board_endpoint_returns_columns(client: TestClient, auth_override) -> None:
    board = SimpleNamespace(
        columns=[
            SimpleNamespace(key="hoy", label="Hoy", count=1, tasks=[_task()]),
            SimpleNamespace(key="vencidas", label="Vencidas", count=0, tasks=[]),
        ],
        total=1,
    )
    with patch("app.modules.automation.router.AutomationService") as Svc:
        svc_instance = MagicMock()
        svc_instance.board = AsyncMock(return_value=board)
        Svc.return_value = svc_instance
        from app.modules.automation.dependencies import get_db_session
        async def _db():
            yield MagicMock()
        client.app.dependency_overrides[get_db_session] = _db
        resp = client.get("/automation/tasks/board")
        assert resp.status_code == 200
        body = resp.json()
        assert body["columns"][0]["key"] == "hoy"
        assert body["total"] == 1


def test_create_task_201(client: TestClient, auth_override) -> None:
    with patch("app.modules.automation.router.AutomationService") as Svc:
        svc_instance = MagicMock()
        svc_instance.create_task = AsyncMock(return_value=_task(title="Llamar al cliente"))
        Svc.return_value = svc_instance
        from app.modules.automation.dependencies import get_db_session
        async def _db():
            yield MagicMock()
        client.app.dependency_overrides[get_db_session] = _db
        resp = client.post(
            "/automation/tasks",
            json={"title": "Llamar al cliente", "task_type": "call", "priority": "high"},
        )
        assert resp.status_code == 201
        assert resp.json()["title"] == "Llamar al cliente"


def test_complete_task_endpoint(client: TestClient, auth_override) -> None:
    task = _task(status="completed")
    with patch("app.modules.automation.router.AutomationService") as Svc:
        svc_instance = MagicMock()
        svc_instance.complete_task = AsyncMock(return_value=task)
        Svc.return_value = svc_instance
        from app.modules.automation.dependencies import get_db_session
        async def _db():
            yield MagicMock()
        client.app.dependency_overrides[get_db_session] = _db
        resp = client.post(f"/automation/tasks/{task.id}/complete")
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"


def test_cancel_task_endpoint(client: TestClient, auth_override) -> None:
    task = _task(status="cancelled")
    with patch("app.modules.automation.router.AutomationService") as Svc:
        svc_instance = MagicMock()
        svc_instance.cancel_task = AsyncMock(return_value=task)
        Svc.return_value = svc_instance
        from app.modules.automation.dependencies import get_db_session
        async def _db():
            yield MagicMock()
        client.app.dependency_overrides[get_db_session] = _db
        resp = client.post(f"/automation/tasks/{task.id}/cancel")
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"


# ─────────────────────────────────────────────────────────────────────────────
# Calendar + events + metrics
# ─────────────────────────────────────────────────────────────────────────────
def test_calendar_endpoint_week(client: TestClient, auth_override) -> None:
    cal = SimpleNamespace(
        view="week", range_start=datetime.now(timezone.utc), range_end=datetime.now(timezone.utc),
        entries=[], total=0,
    )
    with patch("app.modules.automation.router.AutomationService") as Svc:
        svc_instance = MagicMock()
        svc_instance.calendar = AsyncMock(return_value=cal)
        Svc.return_value = svc_instance
        from app.modules.automation.dependencies import get_db_session
        async def _db():
            yield MagicMock()
        client.app.dependency_overrides[get_db_session] = _db
        resp = client.get("/automation/calendar?view=week")
        assert resp.status_code == 200
        assert resp.json()["view"] == "week"


def test_calendar_endpoint_rejects_invalid_view(client: TestClient, auth_override) -> None:
    from app.modules.automation.dependencies import get_db_session
    async def _db():
        yield MagicMock()
    client.app.dependency_overrides[get_db_session] = _db
    resp = client.get("/automation/calendar?view=year")
    assert resp.status_code == 422


def test_events_endpoint(client: TestClient, auth_override) -> None:
    ev = SimpleNamespace(
        id=uuid4(), empresa_id=EMPRESA_ID, rule_id=None, rule_key="LEAD_NO_RESPONSE_24H",
        event_type="lead_idle", entity_type="customer", entity_id=uuid4(),
        severity="warning", payload={}, created_at=datetime.now(timezone.utc),
    )
    with patch("app.modules.automation.router.AutomationService") as Svc:
        svc_instance = MagicMock()
        svc_instance.list_events = AsyncMock(return_value=[ev])
        Svc.return_value = svc_instance
        from app.modules.automation.dependencies import get_db_session
        async def _db():
            yield MagicMock()
        client.app.dependency_overrides[get_db_session] = _db
        resp = client.get("/automation/events?severity=warning")
        assert resp.status_code == 200
        assert resp.json()[0]["rule_key"] == "LEAD_NO_RESPONSE_24H"


def test_metrics_endpoint(client: TestClient, auth_override) -> None:
    metrics = SimpleNamespace(
        tasks_total=10, tasks_pending=7, tasks_today=3, tasks_this_week=10,
        tasks_overdue=1, tasks_completed=3, tasks_completion_rate_pct=30.0,
        alerts_total=12, alerts_critical=2, rules_enabled=6, rules_total=7,
        automation_executions=12, leads_recovered=2, won_after_automation=1,
        average_completion_hours=4.5, by_priority={"high": 2}, by_task_type={"alert": 1},
    )
    with patch("app.modules.automation.router.AutomationService") as Svc:
        svc_instance = MagicMock()
        svc_instance.metrics = AsyncMock(return_value=metrics)
        Svc.return_value = svc_instance
        from app.modules.automation.dependencies import get_db_session
        async def _db():
            yield MagicMock()
        client.app.dependency_overrides[get_db_session] = _db
        resp = client.get("/automation/metrics")
        assert resp.status_code == 200
        body = resp.json()
        assert body["tasks_total"] == 10
        assert body["rules_enabled"] == 6
        assert body["alerts_critical"] == 2
