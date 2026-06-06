"""Integration tests for the Reporting API.

Covers all 10 endpoints (``/reporting/{executive,pipeline,crm,sales,inventory}/{pdf,excel}``)
plus permission gating, tenant isolation, and error handling.
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errors import register_exception_handlers
from app.core.security.dependencies import TenantContext, get_tenant_context
from app.core.security.permissions import ROLE_PERMISSIONS
from app.database.session import get_db_session
from app.modules.reporting.dependencies import (
    get_reporting_service,
    reporting_read_dep,
)
from app.modules.reporting.router import router as reporting_router
from app.modules.reporting.schemas import (
    ExecutiveReportData,
    ReportKPI,
    ReportMetadata,
    ReportSection,
    ReportTable,
)


REPORTING_TENANT = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
REPORTING_USER = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")


def _tenant(roles: list[str] | None = None) -> TenantContext:
    roles = roles or ["owner"]
    perms = set(ROLE_PERMISSIONS.get(roles[0], set())) if roles else set()
    for r in roles[1:]:
        perms.update(ROLE_PERMISSIONS.get(r, set()))
    return TenantContext(
        empresa_id=REPORTING_TENANT,
        user_id=REPORTING_USER,
        roles=roles,
        permissions=perms,
    )


def _build_data() -> ExecutiveReportData:
    return ExecutiveReportData(
        metadata=ReportMetadata(
            generated_at=datetime(2026, 6, 6, 10, 0, tzinfo=timezone.utc),
            tenant_id=REPORTING_TENANT,
            tenant_name="Acme Fashion",
            tenant_logo_url="https://cdn.example.com/acme.png",
            period_label="Hoy: 2026-06-06",
            currency="PEN",
        ),
        kpis=[
            ReportKPI(label="Ventas hoy", value="S/ 100.00", secondary="3 pedidos"),
        ],
        sections=[
            ReportSection(
                title="Resumen",
                kpis=[ReportKPI(label="Total", value="100")],
                tables=[
                    ReportTable(
                        title="Detalle",
                        columns=["A", "B"],
                        rows=[["1", "2"]],
                    )
                ],
            )
        ],
        ai_recommendations=[],
        critical_alerts=[],
    )


def _build_app(svc: MagicMock | None = None) -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(reporting_router, prefix="/api/v1/reporting")
    if svc is None:
        svc = MagicMock()

    async def _db():
        yield AsyncMock()

    async def _svc_override(_db=AsyncMock()):
        return svc

    app.dependency_overrides[get_db_session] = _db
    app.dependency_overrides[get_tenant_context] = lambda: _tenant(["owner"])
    app.dependency_overrides[reporting_read_dep] = lambda: _tenant(["owner"])
    app.dependency_overrides[get_reporting_service] = _svc_override
    return app


def _patch_service_methods(svc: MagicMock) -> None:
    for method in (
        "build_executive_report",
        "build_pipeline_report",
        "build_crm_report",
        "build_sales_report",
        "build_inventory_report",
    ):
        setattr(svc, method, AsyncMock(return_value=_build_data()))


# ---------------------------------------------------------------------------
# All 10 endpoints
# ---------------------------------------------------------------------------
ENDPOINTS = [
    ("/api/v1/reporting/executive/pdf", "application/pdf"),
    ("/api/v1/reporting/executive/excel",
     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ("/api/v1/reporting/pipeline/pdf", "application/pdf"),
    ("/api/v1/reporting/pipeline/excel",
     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ("/api/v1/reporting/crm/pdf", "application/pdf"),
    ("/api/v1/reporting/crm/excel",
     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ("/api/v1/reporting/sales/pdf", "application/pdf"),
    ("/api/v1/reporting/sales/excel",
     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ("/api/v1/reporting/inventory/pdf", "application/pdf"),
    ("/api/v1/reporting/inventory/excel",
     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
]


class TestEndpointContracts:
    @pytest.mark.parametrize("path,content_type", ENDPOINTS)
    def test_endpoint_returns_expected_content_type(
        self, path: str, content_type: str
    ) -> None:
        svc = MagicMock()
        _patch_service_methods(svc)
        app = _build_app(svc=svc)
        client = TestClient(app)
        r = client.get(path)
        assert r.status_code == 200, f"{path} -> {r.status_code} {r.text[:200]}"
        assert r.headers["content-type"].startswith(content_type)
        # Each report is non-empty
        assert len(r.content) > 500

    @pytest.mark.parametrize("path,content_type", ENDPOINTS)
    def test_endpoint_sets_content_disposition_attachment(
        self, path: str, content_type: str
    ) -> None:
        svc = MagicMock()
        _patch_service_methods(svc)
        app = _build_app(svc=svc)
        client = TestClient(app)
        r = client.get(path)
        assert "attachment" in r.headers.get("content-disposition", "")
        # Filename must be present
        assert "filename=" in r.headers.get("content-disposition", "")

    @pytest.mark.parametrize("path,_", ENDPOINTS)
    def test_endpoint_passes_tenant_id_to_service(self, path: str, _: str) -> None:
        svc = MagicMock()
        _patch_service_methods(svc)
        app = _build_app(svc=svc)
        client = TestClient(app)
        client.get(path)
        # Find which method was called
        called = [
            m for m in (
                "build_executive_report",
                "build_pipeline_report",
                "build_crm_report",
                "build_sales_report",
                "build_inventory_report",
            )
            if getattr(svc, m).await_count > 0
        ]
        assert len(called) == 1
        method_name = called[0]
        method = getattr(svc, method_name)
        kwargs = method.await_args.kwargs
        assert kwargs.get("empresa_id") == REPORTING_TENANT

    def test_pdf_endpoint_returns_pdf_magic(self) -> None:
        svc = MagicMock()
        _patch_service_methods(svc)
        app = _build_app(svc=svc)
        client = TestClient(app)
        r = client.get("/api/v1/reporting/executive/pdf")
        assert r.content[:4] == b"%PDF"

    def test_xlsx_endpoint_returns_zip_magic(self) -> None:
        svc = MagicMock()
        _patch_service_methods(svc)
        app = _build_app(svc=svc)
        client = TestClient(app)
        r = client.get("/api/v1/reporting/executive/excel")
        assert r.content[:4] == b"PK\x03\x04"


# ---------------------------------------------------------------------------
# Permission gating
# ---------------------------------------------------------------------------
class TestPermissions:
    def test_analyst_with_reports_read_is_allowed(self) -> None:
        svc = MagicMock()
        _patch_service_methods(svc)
        app = _build_app(svc=svc)
        # Override the read dep with an analyst tenant
        analyst = _tenant(["analyst"])
        assert "reports:read" in analyst.permissions
        app.dependency_overrides[reporting_read_dep] = lambda: analyst
        client = TestClient(app)
        r = client.get("/api/v1/reporting/executive/pdf")
        assert r.status_code == 200

    def test_role_without_reports_read_is_forbidden(self) -> None:
        # Build a tenant context with empty permissions (no reports:read)
        forbidden = TenantContext(
            empresa_id=REPORTING_TENANT,
            user_id=REPORTING_USER,
            roles=["external"],
            permissions=set(),
        )
        app = _build_app()
        # Override only the tenant context (so the real reports:read dep
        # still runs and rejects).
        app.dependency_overrides[get_tenant_context] = lambda: forbidden
        # Make sure the real read dep is NOT overridden
        app.dependency_overrides.pop(reporting_read_dep, None)
        client = TestClient(app)
        r = client.get("/api/v1/reporting/executive/pdf")
        assert r.status_code == 403

    def test_no_tenant_returns_401(self) -> None:
        app = _build_app()
        # Remove the tenant context override to force real auth check
        app.dependency_overrides.pop(get_tenant_context, None)
        app.dependency_overrides.pop(reporting_read_dep, None)
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/v1/reporting/executive/pdf")
        assert r.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Tenant isolation
# ---------------------------------------------------------------------------
class TestTenantIsolation:
    def test_different_tenant_only_sees_own_data(self) -> None:
        svc = MagicMock()

        async def _fake_report(empresa_id: UUID, **_kwargs):
            data = _build_data()
            data.metadata.tenant_id = empresa_id
            return data

        svc.build_executive_report = AsyncMock(side_effect=_fake_report)
        app = _build_app(svc=svc)
        # Use a different tenant for the request
        other_tenant = TenantContext(
            empresa_id=UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc"),
            user_id=REPORTING_USER,
            roles=["owner"],
            permissions=ROLE_PERMISSIONS["owner"],
        )
        app.dependency_overrides[get_tenant_context] = lambda: other_tenant
        app.dependency_overrides[reporting_read_dep] = lambda: other_tenant
        client = TestClient(app)
        client.get("/api/v1/reporting/executive/pdf")
        # The service was called with the OTHER tenant's id, not the default
        kwargs = svc.build_executive_report.await_args.kwargs
        assert kwargs.get("empresa_id") == other_tenant.empresa_id


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------
class TestErrorHandling:
    def test_service_exception_returns_500(self) -> None:
        svc = MagicMock()
        svc.build_executive_report = AsyncMock(side_effect=RuntimeError("boom"))
        app = _build_app(svc=svc)
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/v1/reporting/executive/pdf")
        assert r.status_code in (500, 502)

    def test_xlsx_endpoint_works(self) -> None:
        svc = MagicMock()
        _patch_service_methods(svc)
        app = _build_app(svc=svc)
        client = TestClient(app)
        r = client.get("/api/v1/reporting/inventory/excel")
        assert r.status_code == 200
        assert r.content[:4] == b"PK\x03\x04"


# ---------------------------------------------------------------------------
# Filename generation
# ---------------------------------------------------------------------------
class TestFilenameGeneration:
    def test_pdf_filename_ends_with_pdf(self) -> None:
        svc = MagicMock()
        _patch_service_methods(svc)
        app = _build_app(svc=svc)
        client = TestClient(app)
        r = client.get("/api/v1/reporting/sales/pdf")
        cd = r.headers.get("content-disposition", "")
        assert ".pdf" in cd

    def test_excel_filename_ends_with_xlsx(self) -> None:
        svc = MagicMock()
        _patch_service_methods(svc)
        app = _build_app(svc=svc)
        client = TestClient(app)
        r = client.get("/api/v1/reporting/sales/excel")
        cd = r.headers.get("content-disposition", "")
        assert ".xlsx" in cd
