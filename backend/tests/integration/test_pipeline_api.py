"""Integration tests for the Pipeline API.

These tests build a standalone FastAPI app with the pipeline router
and override dependencies so the suite runs without a live database.
The pipeline ``Service`` is replaced by an ``AsyncMock`` so we can
exhaustively exercise the contract (CRUD, board, metrics, funnel,
alerts, recommendations, dashboard, permissions).
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errors import register_exception_handlers
from app.core.security.dependencies import TenantContext, get_tenant_context
from app.database.session import get_db_session
from app.modules.pipeline.dependencies import (
    pipeline_metrics_dep,
    pipeline_read_dep,
    pipeline_write_dep,
)
from app.modules.pipeline.router import router as pipeline_router
from app.modules.pipeline.schemas import (
    AIScoreBreakdown,
    PipelineAlert,
    PipelineFunnelResponse,
    PipelineMetricsResponse,
    PipelineRecommendation,
)


TENANT = TenantContext(
    empresa_id=UUID("11111111-1111-4111-8111-111111111111"),
    user_id=UUID("22222222-2222-4222-8222-222222222222"),
    roles=["owner"],
    permissions={"pipeline:read", "pipeline:write", "pipeline:metrics"},
)


READ_ONLY_TENANT = TenantContext(
    empresa_id=TENANT.empresa_id,
    user_id=TENANT.user_id,
    roles=["analyst"],
    permissions={"pipeline:read", "pipeline:metrics"},
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_deal_dict(**overrides) -> dict:
    base = {
        "id": str(uuid4()),
        "empresa_id": str(TENANT.empresa_id),
        "customer_id": None,
        "conversation_id": None,
        "order_id": None,
        "title": "Test deal",
        "estimated_value": Decimal("500"),
        "probability": 40,
        "stage": "qualified",
        "stage_entered_at": datetime.now(timezone.utc).isoformat(),
        "last_activity_at": datetime.now(timezone.utc).isoformat(),
        "notes": None,
        "won_reason": None,
        "lost_reason": None,
        "position": 0,
        "channel": "whatsapp",
        "is_vip": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "customer": None,
        "ai_score": None,
    }
    base.update(overrides)
    return base


def _make_fake_service() -> MagicMock:
    svc = MagicMock()
    svc.session = AsyncMock()
    return svc


def _build_app(svc: MagicMock | None = None) -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(pipeline_router, prefix="/api/v1/pipeline")
    if svc is None:
        svc = _make_fake_service()

    async def _tenant():
        return TENANT

    async def _db():
        yield AsyncMock()

    app.dependency_overrides[get_tenant_context] = _tenant
    app.dependency_overrides[get_db_session] = _db
    # NOTE: pipeline_read_dep / pipeline_write_dep / pipeline_metrics_dep are
    # NOT overridden here, so the real ``require_permission`` closures run
    # and enforce the permission checks. Tests that need to bypass auth
    # (e.g. to inject fake services) override these callables explicitly.
    return app


def _override_tenant(app: FastAPI, tenant: TenantContext) -> None:
    """Bypass the permission check entirely. Use only when the test
    intends to validate the service layer, not the auth layer."""
    async def _t():
        return tenant

    app.dependency_overrides[get_tenant_context] = _t
    app.dependency_overrides[pipeline_read_dep] = _t
    app.dependency_overrides[pipeline_write_dep] = _t
    app.dependency_overrides[pipeline_metrics_dep] = _t


# ---------------------------------------------------------------------------
# Stages
# ---------------------------------------------------------------------------
def test_api_get_stages_returns_seven() -> None:
    app = _build_app()
    with TestClient(app) as c:
        r = c.get("/api/v1/pipeline/stages")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 7
        assert {s["key"] for s in data} == {
            "new_lead", "contacted", "qualified", "proposal",
            "negotiation", "won", "lost",
        }


def test_api_get_stages_have_required_metadata() -> None:
    app = _build_app()
    with TestClient(app) as c:
        data = c.get("/api/v1/pipeline/stages").json()
    for s in data:
        for f in ("key", "label", "description", "is_open",
                  "is_terminal", "order", "default_probability", "color"):
            assert f in s, s


# ---------------------------------------------------------------------------
# CRUD — deals
# ---------------------------------------------------------------------------
def test_api_create_deal_returns_201() -> None:
    app = _build_app()
    fake = _make_fake_service()
    fake.create = AsyncMock(return_value=_make_deal_dict(
        title="New", stage="proposal", estimated_value=Decimal("250"),
        probability=50,
    ))
    with TestClient(app) as c:
        from app.modules.pipeline import router as router_mod
        original = router_mod.PipelineService
        router_mod.PipelineService = lambda db: fake  # type: ignore[assignment]
        try:
            r = c.post(
                "/api/v1/pipeline/deals",
                json={"title": "New", "estimated_value": 250, "probability": 50,
                      "stage": "proposal"},
            )
        finally:
            router_mod.PipelineService = original  # type: ignore[assignment]
        assert r.status_code == 201
        body = r.json()
        assert body["title"] == "New"
        assert body["stage"] == "proposal"
        assert float(body["estimated_value"]) == 250.0


def test_api_create_deal_invalid_stage_returns_422() -> None:
    app = _build_app()
    with TestClient(app) as c:
        r = c.post(
            "/api/v1/pipeline/deals",
            json={"title": "x", "stage": "banana"},
        )
    assert r.status_code == 422


def test_api_get_deal_returns_full_payload() -> None:
    app = _build_app()
    deal_id = uuid4()
    fake = _make_fake_service()
    fake.get = AsyncMock(return_value=_make_deal_dict(
        id=str(deal_id), title="Single", customer={
            "id": str(uuid4()), "full_name": "Jane Doe",
            "email": "j@x.com", "phone": "+51", "whatsapp": None,
            "lead_status": "interested", "priority": "hot",
            "lead_score": 90, "is_vip": True,
            "last_interaction_at": None, "conversation_count": 3,
            "lifetime_value": 1000, "orders_count": 2,
        },
    ))
    with TestClient(app) as c:
        from app.modules.pipeline import router as router_mod
        original = router_mod.PipelineService
        router_mod.PipelineService = lambda db: fake  # type: ignore[assignment]
        try:
            r = c.get(f"/api/v1/pipeline/deals/{deal_id}")
        finally:
            router_mod.PipelineService = original  # type: ignore[assignment]
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == str(deal_id)
    assert body["customer"]["full_name"] == "Jane Doe"
    assert body["customer"]["is_vip"] is True


def test_api_update_deal_returns_updated() -> None:
    app = _build_app()
    deal_id = uuid4()
    fake = _make_fake_service()
    fake.update = AsyncMock(return_value=_make_deal_dict(
        id=str(deal_id), title="Renamed", probability=80,
    ))
    with TestClient(app) as c:
        from app.modules.pipeline import router as router_mod
        original = router_mod.PipelineService
        router_mod.PipelineService = lambda db: fake  # type: ignore[assignment]
        try:
            r = c.patch(
                f"/api/v1/pipeline/deals/{deal_id}",
                json={"title": "Renamed", "probability": 80},
            )
        finally:
            router_mod.PipelineService = original  # type: ignore[assignment]
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == "Renamed"
    assert body["probability"] == 80


def test_api_delete_deal_returns_204() -> None:
    app = _build_app()
    fake = _make_fake_service()
    fake.delete = AsyncMock(return_value=None)
    with TestClient(app) as c:
        from app.modules.pipeline import router as router_mod
        original = router_mod.PipelineService
        router_mod.PipelineService = lambda db: fake  # type: ignore[assignment]
        try:
            r = c.delete(f"/api/v1/pipeline/deals/{uuid4()}")
        finally:
            router_mod.PipelineService = original  # type: ignore[assignment]
    assert r.status_code == 204


def test_api_move_stage_returns_201_with_new_stage() -> None:
    app = _build_app()
    deal_id = uuid4()
    fake = _make_fake_service()
    fake.move_stage = AsyncMock(return_value=_make_deal_dict(
        id=str(deal_id), stage="negotiation", probability=80,
    ))
    with TestClient(app) as c:
        from app.modules.pipeline import router as router_mod
        original = router_mod.PipelineService
        router_mod.PipelineService = lambda db: fake  # type: ignore[assignment]
        try:
            r = c.post(
                f"/api/v1/pipeline/deals/{deal_id}/move-stage",
                json={"target_stage": "negotiation", "probability": 80},
            )
        finally:
            router_mod.PipelineService = original  # type: ignore[assignment]
    assert r.status_code == 200
    assert r.json()["stage"] == "negotiation"


def test_api_move_stage_to_won_carries_reason() -> None:
    app = _build_app()
    deal_id = uuid4()
    fake = _make_fake_service()
    fake.move_stage = AsyncMock(return_value=_make_deal_dict(
        id=str(deal_id), stage="won", won_reason="Fit perfecto",
    ))
    with TestClient(app) as c:
        from app.modules.pipeline import router as router_mod
        original = router_mod.PipelineService
        router_mod.PipelineService = lambda db: fake  # type: ignore[assignment]
        try:
            r = c.post(
                f"/api/v1/pipeline/deals/{deal_id}/move-stage",
                json={"target_stage": "won", "won_reason": "Fit perfecto"},
            )
        finally:
            router_mod.PipelineService = original  # type: ignore[assignment]
    assert r.status_code == 200
    body = r.json()
    assert body["stage"] == "won"
    assert body["won_reason"] == "Fit perfecto"


# ---------------------------------------------------------------------------
# Board / metrics / funnel / alerts / recommendations / dashboard
# ---------------------------------------------------------------------------
def test_api_board_returns_items_by_stage() -> None:
    app = _build_app()
    fake = _make_fake_service()
    fake.list_board = AsyncMock(return_value=SimpleNamespace(
        items=[_make_deal_dict(stage="new_lead"), _make_deal_dict(stage="won")],
        total=2,
        by_stage={"new_lead": 1, "won": 1},
        value_by_stage={"new_lead": 500.0, "won": 1000.0},
    ))
    with TestClient(app) as c:
        from app.modules.pipeline import router as router_mod
        original = router_mod.PipelineService
        router_mod.PipelineService = lambda db: fake  # type: ignore[assignment]
        try:
            r = c.get("/api/v1/pipeline/board")
        finally:
            router_mod.PipelineService = original  # type: ignore[assignment]
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert body["by_stage"]["new_lead"] == 1
    assert body["value_by_stage"]["won"] == 1000.0


def test_api_board_filter_by_stage() -> None:
    app = _build_app()
    fake = _make_fake_service()
    fake.list_board = AsyncMock(return_value=SimpleNamespace(
        items=[], total=0,
        by_stage={"new_lead": 0}, value_by_stage={"new_lead": 0.0},
    ))
    with TestClient(app) as c:
        from app.modules.pipeline import router as router_mod
        original = router_mod.PipelineService
        router_mod.PipelineService = lambda db: fake  # type: ignore[assignment]
        try:
            r = c.get("/api/v1/pipeline/board?stage=new_lead")
        finally:
            router_mod.PipelineService = original  # type: ignore[assignment]
    assert r.status_code == 200
    assert fake.list_board.await_args.kwargs.get("stage") == "new_lead"


def test_api_metrics_returns_required_fields() -> None:
    app = _build_app()
    fake = _make_fake_service()
    fake.metrics = AsyncMock(return_value=PipelineMetricsResponse(
        total_open=5, total_closed_won=3, total_closed_lost=1, new_leads=2,
        open_value=1000.0, weighted_open_value=400.0, won_value=3000.0,
        lost_value=500.0, conversion_rate_pct=75.0, average_deal_value=562.5,
        average_time_to_close_days=12.0,
        average_time_in_current_stage_days=3.0, oldest_unstuck_days=14,
        alerts_count=2, by_stage={}, by_channel={}, by_priority={},
    ))
    with TestClient(app) as c:
        from app.modules.pipeline import router as router_mod
        original = router_mod.PipelineService
        router_mod.PipelineService = lambda db: fake  # type: ignore[assignment]
        try:
            r = c.get("/api/v1/pipeline/metrics")
        finally:
            router_mod.PipelineService = original  # type: ignore[assignment]
    assert r.status_code == 200
    body = r.json()
    for field in (
        "total_open", "total_closed_won", "total_closed_lost",
        "new_leads", "open_value", "weighted_open_value",
        "won_value", "lost_value", "conversion_rate_pct",
        "average_time_to_close_days", "alerts_count",
    ):
        assert field in body, field
    assert body["new_leads"] == 2
    assert body["conversion_rate_pct"] == 75.0


def test_api_funnel_returns_stages() -> None:
    app = _build_app()
    fake = _make_fake_service()
    fake.funnel = AsyncMock(return_value=PipelineFunnelResponse(
        stages=[
            {"key": "new_lead", "label": "Nuevo", "color": "#aaa",
             "count": 3, "value": 1500.0},
        ],
        total_open=3, total_closed=0, won_value=0.0, lost_value=0.0,
    ))
    with TestClient(app) as c:
        from app.modules.pipeline import router as router_mod
        original = router_mod.PipelineService
        router_mod.PipelineService = lambda db: fake  # type: ignore[assignment]
        try:
            r = c.get("/api/v1/pipeline/funnel")
        finally:
            router_mod.PipelineService = original  # type: ignore[assignment]
    assert r.status_code == 200
    body = r.json()
    assert "stages" in body
    assert body["stages"][0]["key"] == "new_lead"


def test_api_alerts_returns_list() -> None:
    app = _build_app()
    fake = _make_fake_service()
    fake.alerts = AsyncMock(return_value=SimpleNamespace(
        alerts=[
            PipelineAlert(
                id="x", deal_id=uuid4(), deal_title="Stuck",
                customer_id=None, rule="STUCK_IN_STAGE", severity="warning",
                message="stuck", suggested_action="act",
                stage="qualified", days_in_stage=10,
                created_at=datetime.now(timezone.utc),
            ),
        ],
        total=1,
    ))
    with TestClient(app) as c:
        from app.modules.pipeline import router as router_mod
        original = router_mod.PipelineService
        router_mod.PipelineService = lambda db: fake  # type: ignore[assignment]
        try:
            r = c.get("/api/v1/pipeline/alerts")
        finally:
            router_mod.PipelineService = original  # type: ignore[assignment]
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["alerts"][0]["rule"] == "STUCK_IN_STAGE"


def test_api_recommendations_returns_scored_list() -> None:
    app = _build_app()
    fake = _make_fake_service()
    fake.recommendations = AsyncMock(return_value=SimpleNamespace(
        recommendations=[
            PipelineRecommendation(
                deal_id=uuid4(), score=82,
                breakdown=AIScoreBreakdown(
                    total=82, intent=80, engagement=70, recency=85,
                    monetary=75, sentiment=80, rationale=["high intent"],
                ),
                next_best_action="Enviar propuesta",
                suggested_channel="WhatsApp", suggested_stage="proposal",
                notes=["high intent"],
            ),
        ],
        total=1,
    ))
    with TestClient(app) as c:
        from app.modules.pipeline import router as router_mod
        original = router_mod.PipelineService
        router_mod.PipelineService = lambda db: fake  # type: ignore[assignment]
        try:
            r = c.get("/api/v1/pipeline/recommendations")
        finally:
            router_mod.PipelineService = original  # type: ignore[assignment]
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["recommendations"][0]["score"] == 82
    assert body["recommendations"][0]["next_best_action"] == "Enviar propuesta"


def test_api_ai_score_returns_breakdown() -> None:
    app = _build_app()
    deal_id = uuid4()
    fake = _make_fake_service()
    fake.score = AsyncMock(return_value=SimpleNamespace(
        deal_id=deal_id, score=77,
        breakdown=AIScoreBreakdown(
            total=77, intent=70, engagement=60, recency=80, monetary=90,
            sentiment=70,
        ),
    ))
    with TestClient(app) as c:
        from app.modules.pipeline import router as router_mod
        original = router_mod.PipelineService
        router_mod.PipelineService = lambda db: fake  # type: ignore[assignment]
        try:
            r = c.post(f"/api/v1/pipeline/deals/{deal_id}/ai-score")
        finally:
            router_mod.PipelineService = original  # type: ignore[assignment]
    assert r.status_code == 200
    body = r.json()
    assert body["score"] == 77
    assert body["breakdown"]["monetary"] == 90


def test_api_dashboard_aggregates_payload() -> None:
    app = _build_app()
    fake = _make_fake_service()
    fake.dashboard = AsyncMock(return_value=SimpleNamespace(
        metrics=PipelineMetricsResponse(
            total_open=2, total_closed_won=1, total_closed_lost=0, new_leads=1,
            open_value=500.0, weighted_open_value=200.0, won_value=300.0,
            lost_value=0.0, conversion_rate_pct=100.0, average_deal_value=200.0,
            average_time_to_close_days=5.0,
            average_time_in_current_stage_days=2.0, oldest_unstuck_days=0,
            alerts_count=0, by_stage={}, by_channel={}, by_priority={},
        ),
        funnel=SimpleNamespace(stages=[], total_open=2, total_closed=1,
                               won_value=300.0, lost_value=0.0),
        alerts=SimpleNamespace(alerts=[], total=0),
        top_deals=[_make_deal_dict()],
        generated_at=datetime.now(timezone.utc),
    ))
    with TestClient(app) as c:
        from app.modules.pipeline import router as router_mod
        original = router_mod.PipelineService
        router_mod.PipelineService = lambda db: fake  # type: ignore[assignment]
        try:
            r = c.get("/api/v1/pipeline/dashboard")
        finally:
            router_mod.PipelineService = original  # type: ignore[assignment]
    assert r.status_code == 200
    body = r.json()
    assert "metrics" in body
    assert "funnel" in body
    assert "alerts" in body
    assert "top_deals" in body
    assert body["metrics"]["new_leads"] == 1


# ---------------------------------------------------------------------------
# Permissions — override only the underlying ``get_tenant_context`` so that
# the actual ``require_permission`` closure still runs.
# ---------------------------------------------------------------------------
def _override_underlying_tenant(app: FastAPI, tenant: TenantContext) -> None:
    async def _t():
        return tenant

    app.dependency_overrides[get_tenant_context] = _t


def test_api_analyst_cannot_create_deal_returns_403() -> None:
    app = _build_app()
    _override_underlying_tenant(app, READ_ONLY_TENANT)
    with TestClient(app) as c:
        r = c.post(
            "/api/v1/pipeline/deals",
            json={"title": "x"},
        )
    assert r.status_code == 403


def test_api_analyst_cannot_move_stage_returns_403() -> None:
    app = _build_app()
    _override_underlying_tenant(app, READ_ONLY_TENANT)
    with TestClient(app) as c:
        r = c.post(
            f"/api/v1/pipeline/deals/{uuid4()}/move-stage",
            json={"target_stage": "negotiation"},
        )
    assert r.status_code == 403


def test_api_analyst_can_read_metrics() -> None:
    app = _build_app()
    _override_underlying_tenant(app, READ_ONLY_TENANT)
    fake = _make_fake_service()
    fake.metrics = AsyncMock(return_value=PipelineMetricsResponse(
        total_open=0, total_closed_won=0, total_closed_lost=0, new_leads=0,
        open_value=0.0, weighted_open_value=0.0, won_value=0.0, lost_value=0.0,
        conversion_rate_pct=0.0, average_deal_value=0.0,
        average_time_to_close_days=0.0, average_time_in_current_stage_days=0.0,
        oldest_unstuck_days=0, alerts_count=0,
        by_stage={}, by_channel={}, by_priority={},
    ))
    with TestClient(app) as c:
        from app.modules.pipeline import router as router_mod
        original = router_mod.PipelineService
        router_mod.PipelineService = lambda db: fake  # type: ignore[assignment]
        try:
            r = c.get("/api/v1/pipeline/metrics")
        finally:
            router_mod.PipelineService = original  # type: ignore[assignment]
    assert r.status_code == 200


def test_api_tenant_without_pipeline_read_returns_403() -> None:
    app = _build_app()
    empty_tenant = TenantContext(
        empresa_id=TENANT.empresa_id, user_id=TENANT.user_id,
        roles=["viewer"], permissions=set(),
    )
    _override_underlying_tenant(app, empty_tenant)
    with TestClient(app) as c:
        r = c.get("/api/v1/pipeline/stages")
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# Validation of input payload shapes
# ---------------------------------------------------------------------------
def test_api_create_deal_rejects_negative_value() -> None:
    app = _build_app()
    with TestClient(app) as c:
        r = c.post(
            "/api/v1/pipeline/deals",
            json={"title": "x", "estimated_value": -1, "probability": 50},
        )
    assert r.status_code == 422


def test_api_create_deal_rejects_probability_above_100() -> None:
    app = _build_app()
    with TestClient(app) as c:
        r = c.post(
            "/api/v1/pipeline/deals",
            json={"title": "x", "probability": 150},
        )
    assert r.status_code == 422


def test_api_create_deal_rejects_empty_title() -> None:
    app = _build_app()
    with TestClient(app) as c:
        r = c.post(
            "/api/v1/pipeline/deals",
            json={"title": ""},
        )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# OpenAPI surface — every endpoint documented
# ---------------------------------------------------------------------------
def test_api_openapi_documents_all_pipeline_paths() -> None:
    app = _build_app()
    schema = app.openapi()
    paths = set(schema["paths"].keys())
    for path in (
        "/api/v1/pipeline/stages",
        "/api/v1/pipeline/board",
        "/api/v1/pipeline/deals",
        "/api/v1/pipeline/deals/{deal_id}",
        "/api/v1/pipeline/deals/{deal_id}/move-stage",
        "/api/v1/pipeline/deals/{deal_id}/ai-score",
        "/api/v1/pipeline/metrics",
        "/api/v1/pipeline/funnel",
        "/api/v1/pipeline/alerts",
        "/api/v1/pipeline/recommendations",
        "/api/v1/pipeline/dashboard",
    ):
        assert path in paths, f"missing path in OpenAPI: {path}"
