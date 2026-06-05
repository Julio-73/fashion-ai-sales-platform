"""Integration tests for the Executive Dashboard API.

Covers the FastAPI contract: HTTP status codes, response model
serialization, permission enforcement, and the full JSON payload
shape returned by ``GET /api/v1/executive-dashboard/``.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errors import register_exception_handlers
from app.core.security.dependencies import TenantContext, get_tenant_context
from app.database.session import get_db_session
from app.modules.executive_dashboard.dependencies import (
    executive_dashboard_read_dep,
)
from app.modules.executive_dashboard.router import router as executive_router
from app.modules.executive_dashboard.schemas import ExecutiveDashboardResponse


TENANT = TenantContext(
    empresa_id=UUID("11111111-1111-4111-8111-111111111111"),
    user_id=UUID("22222222-2222-4222-8222-222222222222"),
    roles=["owner"],
    permissions={"analytics:read", "orders:read", "pipeline:read"},
)


ANALYST_TENANT = TenantContext(
    empresa_id=TENANT.empresa_id,
    user_id=TENANT.user_id,
    roles=["analyst"],
    permissions={"analytics:read"},
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _build_app(svc: MagicMock | None = None) -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(executive_router, prefix="/api/v1/executive-dashboard")
    if svc is None:
        svc = MagicMock()

    async def _tenant():
        return TENANT

    async def _db():
        yield AsyncMock()

    async def _svc_override(_db=AsyncMock()):
        return svc

    app.dependency_overrides[get_tenant_context] = _tenant
    app.dependency_overrides[get_db_session] = _db
    app.dependency_overrides[executive_dashboard_read_dep] = _tenant
    app.dependency_overrides[
        __import__(
            "app.modules.executive_dashboard.dependencies",
            fromlist=["get_executive_dashboard_service"],
        ).get_executive_dashboard_service
    ] = _svc_override
    return app


def _universal_response(tenant_id: UUID) -> dict:
    """A complete, plausible executive-dashboard response payload."""
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "period": {
            "today": "2026-06-05T00:00:00+00:00",
            "week_start": "2026-06-01T00:00:00+00:00",
            "month_start": "2026-06-01T00:00:00+00:00",
            "year_start": "2026-01-01T00:00:00+00:00",
        },
        "currency": "PEN",
        "kpis": {
            "sales_today": "100.00",
            "sales_week": "500.00",
            "sales_month": "2000.00",
            "sales_year": "20000.00",
            "average_ticket": "125.50",
            "average_ticket_month": "150.00",
            "active_customers": 25,
            "vip_customers": 4,
            "active_conversations": 7,
            "leads_open": 12,
            "leads_won": 3,
            "leads_lost": 1,
            "conversion_rate_pct": 75.0,
            "total_orders": 90,
        },
        "sales_trend": {
            "daily": [
                {"date": "2026-05-07", "revenue": "0", "orders": 0},
                {"date": "2026-05-08", "revenue": "50", "orders": 1},
            ],
            "monthly": [
                {"month": "2025-07", "revenue": "1000", "orders": 5},
                {"month": "2025-08", "revenue": "1500", "orders": 7},
            ],
        },
        "pipeline": {
            "total_value": "15000.00",
            "weighted_value": "7500.00",
            "won_value": "8000.00",
            "lost_value": "2000.00",
            "conversion_pct": 75.0,
            "average_time_to_close_days": 5.5,
            "open_deals": 12,
            "won_deals": 3,
            "lost_deals": 1,
            "funnel": [
                {
                    "stage": "new_lead",
                    "label": "Nuevo Lead",
                    "count": 4,
                    "value": "2000.00",
                    "order": 1,
                    "color": "#6366f1",
                },
                {
                    "stage": "contacted",
                    "label": "Contactado",
                    "count": 3,
                    "value": "3000.00",
                    "order": 2,
                    "color": "#0ea5e9",
                },
                {
                    "stage": "qualified",
                    "label": "Calificado",
                    "count": 2,
                    "value": "4000.00",
                    "order": 3,
                    "color": "#8b5cf6",
                },
                {
                    "stage": "proposal",
                    "label": "Propuesta",
                    "count": 2,
                    "value": "5000.00",
                    "order": 4,
                    "color": "#f59e0b",
                },
                {
                    "stage": "negotiation",
                    "label": "Negociación",
                    "count": 1,
                    "value": "6000.00",
                    "order": 5,
                    "color": "#ec4899",
                },
                {
                    "stage": "won",
                    "label": "Ganado",
                    "count": 3,
                    "value": "8000.00",
                    "order": 6,
                    "color": "#10b981",
                },
                {
                    "stage": "lost",
                    "label": "Perdido",
                    "count": 1,
                    "value": "2000.00",
                    "order": 7,
                    "color": "#ef4444",
                },
            ],
        },
        "ai_recommendations": [
            {
                "id": "hot_lead:abc",
                "title": "Lead caliente: VIP Deal",
                "description": "Negociación abierta",
                "score": 85,
                "priority": "high",
                "category": "lead_caliente",
                "cta_label": "Abrir trato",
                "cta_href": "/dashboard/pipeline/abc",
            }
        ],
        "forecast": {
            "monthly": {
                "projected_revenue": "2000.00",
                "confidence": "high",
                "basis": "Promedio de los últimos 6 meses",
                "sample_size": 6,
            },
            "quarterly": {
                "projected_revenue": "6000.00",
                "confidence": "high",
                "basis": "Proyección trimestral",
                "sample_size": 6,
            },
        },
        "top_customers": [
            {
                "id": str(uuid4()),
                "full_name": "María Pérez",
                "email": "maria@example.com",
                "phone": "+51999999999",
                "is_vip": True,
                "order_count": 12,
                "lifetime_value": "5400.00",
                "average_ticket": "450.00",
                "days_since_last_purchase": 10,
            }
        ],
        "top_products": {
            "most_sold": [
                {
                    "product_id": str(uuid4()),
                    "name": "Polo Premium",
                    "units_sold": 120,
                    "revenue": "3600.00",
                }
            ],
            "most_profitable": [
                {
                    "product_id": str(uuid4()),
                    "name": "Vestido Floral",
                    "revenue": "4800.00",
                    "units_sold": 80,
                }
            ],
            "most_consulted": [],
        },
        "alerts": {
            "inventory_critical": [
                {
                    "product_id": str(uuid4()),
                    "name": "Producto Agotado",
                    "stock": 0,
                    "min_stock": 5,
                    "status": "out",
                }
            ],
            "leads_abandoned": [
                {
                    "deal_id": str(uuid4()),
                    "title": "Trato viejo",
                    "stage": "negotiation",
                    "days_inactive": 10,
                    "value": "500.00",
                }
            ],
            "conversations_unanswered": [
                {
                    "conversation_id": str(uuid4()),
                    "customer_name": "Cliente A",
                    "channel": "whatsapp",
                    "last_message_at": "2026-06-03T10:00:00+00:00",
                    "hours_silent": 48,
                }
            ],
            "inactive_customers": [
                {
                    "customer_id": str(uuid4()),
                    "full_name": "Cliente Inactivo",
                    "days_inactive": 120,
                    "last_purchase_at": "2026-01-01T00:00:00+00:00",
                }
            ],
            "delayed_orders": [
                {
                    "order_id": str(uuid4()),
                    "order_number": "ORD-001",
                    "customer_name": "Cliente X",
                    "status": "pending",
                    "days_since_created": 5,
                    "total": "250.00",
                }
            ],
        },
        "metadata": {
            "tenant_id": str(TENANT.empresa_id),
            "computed_in_ms": 42,
        },
    }


# ---------------------------------------------------------------------------
# HTTP contract
# ---------------------------------------------------------------------------
class TestHttpContract:
    def test_get_dashboard_returns_200(self) -> None:
        svc = MagicMock()
        response_data = _universal_response(TENANT.empresa_id)
        response_obj = ExecutiveDashboardResponse(**response_data)
        svc.get_dashboard = AsyncMock(return_value=response_obj)
        app = _build_app(svc=svc)
        client = TestClient(app)
        r = client.get("/api/v1/executive-dashboard/")
        assert r.status_code == 200
        body = r.json()
        assert body["currency"] == "PEN"
        assert body["metadata"]["tenant_id"] == str(TENANT.empresa_id)

    def test_response_has_all_top_level_keys(self) -> None:
        svc = MagicMock()
        response_obj = ExecutiveDashboardResponse(**_universal_response(TENANT.empresa_id))
        svc.get_dashboard = AsyncMock(return_value=response_obj)
        app = _build_app(svc=svc)
        client = TestClient(app)
        r = client.get("/api/v1/executive-dashboard/")
        assert r.status_code == 200
        body = r.json()
        for key in (
            "generated_at", "period", "currency", "kpis", "sales_trend",
            "pipeline", "ai_recommendations", "forecast", "top_customers",
            "top_products", "alerts", "metadata",
        ):
            assert key in body, f"Missing key: {key}"

    def test_kpis_keys_present(self) -> None:
        svc = MagicMock()
        response_obj = ExecutiveDashboardResponse(**_universal_response(TENANT.empresa_id))
        svc.get_dashboard = AsyncMock(return_value=response_obj)
        app = _build_app(svc=svc)
        client = TestClient(app)
        body = client.get("/api/v1/executive-dashboard/").json()
        for key in (
            "sales_today", "sales_week", "sales_month", "sales_year",
            "average_ticket", "average_ticket_month",
            "active_customers", "vip_customers", "active_conversations",
            "leads_open", "leads_won", "leads_lost",
            "conversion_rate_pct", "total_orders",
        ):
            assert key in body["kpis"], f"Missing KPI key: {key}"

    def test_pipeline_funnel_has_seven_stages(self) -> None:
        svc = MagicMock()
        response_obj = ExecutiveDashboardResponse(**_universal_response(TENANT.empresa_id))
        svc.get_dashboard = AsyncMock(return_value=response_obj)
        app = _build_app(svc=svc)
        client = TestClient(app)
        body = client.get("/api/v1/executive-dashboard/").json()
        assert len(body["pipeline"]["funnel"]) == 7
        stages = [s["stage"] for s in body["pipeline"]["funnel"]]
        assert stages == [
            "new_lead", "contacted", "qualified", "proposal",
            "negotiation", "won", "lost",
        ]

    def test_alerts_all_sections_present(self) -> None:
        svc = MagicMock()
        response_obj = ExecutiveDashboardResponse(**_universal_response(TENANT.empresa_id))
        svc.get_dashboard = AsyncMock(return_value=response_obj)
        app = _build_app(svc=svc)
        client = TestClient(app)
        body = client.get("/api/v1/executive-dashboard/").json()
        for key in (
            "inventory_critical", "leads_abandoned",
            "conversations_unanswered", "inactive_customers",
            "delayed_orders",
        ):
            assert key in body["alerts"], f"Missing alert key: {key}"
            assert isinstance(body["alerts"][key], list)

    def test_top_products_has_three_lists(self) -> None:
        svc = MagicMock()
        response_obj = ExecutiveDashboardResponse(**_universal_response(TENANT.empresa_id))
        svc.get_dashboard = AsyncMock(return_value=response_obj)
        app = _build_app(svc=svc)
        client = TestClient(app)
        body = client.get("/api/v1/executive-dashboard/").json()
        assert "most_sold" in body["top_products"]
        assert "most_profitable" in body["top_products"]
        assert "most_consulted" in body["top_products"]
        # most_consulted is empty (no product-views table)
        assert body["top_products"]["most_consulted"] == []

    def test_ai_recommendation_priority_in_enum(self) -> None:
        svc = MagicMock()
        response_obj = ExecutiveDashboardResponse(**_universal_response(TENANT.empresa_id))
        svc.get_dashboard = AsyncMock(return_value=response_obj)
        app = _build_app(svc=svc)
        client = TestClient(app)
        body = client.get("/api/v1/executive-dashboard/").json()
        for rec in body["ai_recommendations"]:
            assert rec["priority"] in ("high", "medium", "low")
            assert 0 <= rec["score"] <= 100
            assert rec["cta_label"]

    def test_forecast_confidence_in_enum(self) -> None:
        svc = MagicMock()
        response_obj = ExecutiveDashboardResponse(**_universal_response(TENANT.empresa_id))
        svc.get_dashboard = AsyncMock(return_value=response_obj)
        app = _build_app(svc=svc)
        client = TestClient(app)
        body = client.get("/api/v1/executive-dashboard/").json()
        assert body["forecast"]["monthly"]["confidence"] in ("low", "medium", "high")
        assert body["forecast"]["quarterly"]["confidence"] in ("low", "medium", "high")
        assert body["forecast"]["monthly"]["sample_size"] >= 0


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------
class TestPermissions:
    def test_analyst_role_with_analytics_read_can_access(self) -> None:
        async def _tenant():
            return ANALYST_TENANT

        svc = MagicMock()
        response_obj = ExecutiveDashboardResponse(**_universal_response(TENANT.empresa_id))
        svc.get_dashboard = AsyncMock(return_value=response_obj)

        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(executive_router, prefix="/api/v1/executive-dashboard")

        async def _db():
            yield AsyncMock()

        app.dependency_overrides[get_tenant_context] = _tenant
        app.dependency_overrides[get_db_session] = _db
        app.dependency_overrides[executive_dashboard_read_dep] = _tenant
        app.dependency_overrides[
            __import__(
                "app.modules.executive_dashboard.dependencies",
                fromlist=["get_executive_dashboard_service"],
            ).get_executive_dashboard_service
        ] = lambda _db=AsyncMock(): svc

        client = TestClient(app)
        r = client.get("/api/v1/executive-dashboard/")
        assert r.status_code == 200

    def test_user_without_analytics_read_is_forbidden(self) -> None:
        forbidden_tenant = TenantContext(
            empresa_id=TENANT.empresa_id,
            user_id=TENANT.user_id,
            roles=["external"],
            permissions=set(),  # no permissions
        )

        async def _tenant():
            return forbidden_tenant

        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(executive_router, prefix="/api/v1/executive-dashboard")

        async def _db():
            yield AsyncMock()

        # NOTE: we only override get_tenant_context. The real
        # executive_dashboard_read_dep still runs and checks the
        # permission set.
        app.dependency_overrides[get_tenant_context] = _tenant
        app.dependency_overrides[get_db_session] = _db

        client = TestClient(app)
        r = client.get("/api/v1/executive-dashboard/")
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# Tenant isolation
# ---------------------------------------------------------------------------
class TestTenantIsolation:
    def test_endpoint_passes_tenant_id_to_service(self) -> None:
        svc = MagicMock()
        response_obj = ExecutiveDashboardResponse(**_universal_response(TENANT.empresa_id))
        svc.get_dashboard = AsyncMock(return_value=response_obj)
        app = _build_app(svc=svc)
        client = TestClient(app)
        r = client.get("/api/v1/executive-dashboard/")
        assert r.status_code == 200
        svc.get_dashboard.assert_awaited_once()
        kwargs = svc.get_dashboard.await_args.kwargs
        assert kwargs.get("tenant_id") == TENANT.empresa_id

    def test_metadata_tenant_id_matches_request(self) -> None:
        svc = MagicMock()
        response_obj = ExecutiveDashboardResponse(**_universal_response(TENANT.empresa_id))
        svc.get_dashboard = AsyncMock(return_value=response_obj)
        app = _build_app(svc=svc)
        client = TestClient(app)
        body = client.get("/api/v1/executive-dashboard/").json()
        assert body["metadata"]["tenant_id"] == str(TENANT.empresa_id)


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------
class TestErrorHandling:
    def test_service_error_returns_500(self) -> None:
        svc = MagicMock()
        svc.get_dashboard = AsyncMock(side_effect=RuntimeError("boom"))
        app = _build_app(svc=svc)
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/v1/executive-dashboard/")
        # The platform's exception handlers map unhandled exceptions to 500.
        assert r.status_code in (500, 502)

    def test_missing_tenant_returns_401(self) -> None:
        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(executive_router, prefix="/api/v1/executive-dashboard")

        async def _db():
            yield AsyncMock()

        # No override for get_tenant_context → the real auth dependency runs.
        # Without a Bearer token it raises 401.
        app.dependency_overrides[get_db_session] = _db

        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/v1/executive-dashboard/")
        assert r.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Payload invariants
# ---------------------------------------------------------------------------
class TestPayloadInvariants:
    def test_decimal_fields_are_strings(self) -> None:
        svc = MagicMock()
        response_obj = ExecutiveDashboardResponse(**_universal_response(TENANT.empresa_id))
        svc.get_dashboard = AsyncMock(return_value=response_obj)
        app = _build_app(svc=svc)
        client = TestClient(app)
        body = client.get("/api/v1/executive-dashboard/").json()
        # Decimals are serialized as strings to preserve precision.
        assert isinstance(body["kpis"]["sales_today"], str)
        assert isinstance(body["pipeline"]["total_value"], str)
        assert isinstance(body["top_customers"][0]["lifetime_value"], str)

    def test_30_day_trend_does_not_crash(self) -> None:
        svc = MagicMock()
        response_obj = ExecutiveDashboardResponse(**_universal_response(TENANT.empresa_id))
        svc.get_dashboard = AsyncMock(return_value=response_obj)
        app = _build_app(svc=svc)
        client = TestClient(app)
        body = client.get("/api/v1/executive-dashboard/").json()
        # daily/monthly fields exist; length can be 0 if there's no data
        assert isinstance(body["sales_trend"]["daily"], list)
        assert isinstance(body["sales_trend"]["monthly"], list)

    def test_currency_is_pen(self) -> None:
        svc = MagicMock()
        response_obj = ExecutiveDashboardResponse(**_universal_response(TENANT.empresa_id))
        svc.get_dashboard = AsyncMock(return_value=response_obj)
        app = _build_app(svc=svc)
        client = TestClient(app)
        body = client.get("/api/v1/executive-dashboard/").json()
        assert body["currency"] == "PEN"

    def test_computed_in_ms_is_non_negative(self) -> None:
        svc = MagicMock()
        response_obj = ExecutiveDashboardResponse(**_universal_response(TENANT.empresa_id))
        svc.get_dashboard = AsyncMock(return_value=response_obj)
        app = _build_app(svc=svc)
        client = TestClient(app)
        body = client.get("/api/v1/executive-dashboard/").json()
        assert body["metadata"]["computed_in_ms"] >= 0
