"""FastAPI router — Reporting module.

Ten endpoints mounted under ``/reporting`` (see
``app/api/router.py``). Each pair (executive, pipeline, crm, sales,
inventory) returns a fully-formed PDF or XLSX file via ``FileResponse``.

The endpoints never mutate state. All aggregations are tenant-scoped
via ``empresa_id`` taken from the request context.
"""
from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter
from fastapi.responses import Response

from app.modules.reporting.dependencies import (
    ReportingReadContext,
    ReportingServiceDep,
)
from app.modules.reporting.generators.pdf_generator import build_executive_pdf
from app.modules.reporting.generators.xlsx_generator import build_executive_xlsx


router = APIRouter()


def _filename(report: str, fmt: str) -> str:
    ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    return f"{report}-{ts}.{fmt}"


def _pdf_response(data, *, report: str) -> Response:
    pdf_bytes = build_executive_pdf(data)
    filename = _filename(report, "pdf")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
            "X-Report-Generated-At": data.metadata.generated_at.isoformat(),
        },
    )


def _xlsx_response(data, *, report: str) -> Response:
    xlsx_bytes = build_executive_xlsx(data)
    filename = _filename(report, "xlsx")
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(xlsx_bytes)),
            "X-Report-Generated-At": data.metadata.generated_at.isoformat(),
        },
    )


# ---------------------------------------------------------------------------
# Executive
# ---------------------------------------------------------------------------
@router.get(
    "/executive/pdf",
    summary="Descargar reporte ejecutivo en PDF",
    response_class=Response,
)
async def executive_pdf(
    tenant: ReportingReadContext,
    service: ReportingServiceDep,
) -> Response:
    data = await service.build_executive_report(empresa_id=tenant.empresa_id)
    return _pdf_response(data, report="executive")


@router.get(
    "/executive/excel",
    summary="Descargar reporte ejecutivo en Excel (multi-hoja)",
    response_class=Response,
)
async def executive_excel(
    tenant: ReportingReadContext,
    service: ReportingServiceDep,
) -> Response:
    data = await service.build_executive_report(empresa_id=tenant.empresa_id)
    return _xlsx_response(data, report="executive")


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
@router.get(
    "/pipeline/pdf",
    summary="Descargar reporte de pipeline en PDF",
    response_class=Response,
)
async def pipeline_pdf(
    tenant: ReportingReadContext,
    service: ReportingServiceDep,
) -> Response:
    data = await service.build_pipeline_report(empresa_id=tenant.empresa_id)
    return _pdf_response(data, report="pipeline")


@router.get(
    "/pipeline/excel",
    summary="Descargar reporte de pipeline en Excel",
    response_class=Response,
)
async def pipeline_excel(
    tenant: ReportingReadContext,
    service: ReportingServiceDep,
) -> Response:
    data = await service.build_pipeline_report(empresa_id=tenant.empresa_id)
    return _xlsx_response(data, report="pipeline")


# ---------------------------------------------------------------------------
# CRM
# ---------------------------------------------------------------------------
@router.get(
    "/crm/pdf",
    summary="Descargar reporte de clientes / CRM en PDF",
    response_class=Response,
)
async def crm_pdf(
    tenant: ReportingReadContext,
    service: ReportingServiceDep,
) -> Response:
    data = await service.build_crm_report(empresa_id=tenant.empresa_id)
    return _pdf_response(data, report="crm")


@router.get(
    "/crm/excel",
    summary="Descargar reporte de clientes / CRM en Excel",
    response_class=Response,
)
async def crm_excel(
    tenant: ReportingReadContext,
    service: ReportingServiceDep,
) -> Response:
    data = await service.build_crm_report(empresa_id=tenant.empresa_id)
    return _xlsx_response(data, report="crm")


# ---------------------------------------------------------------------------
# Sales
# ---------------------------------------------------------------------------
@router.get(
    "/sales/pdf",
    summary="Descargar reporte de ventas en PDF",
    response_class=Response,
)
async def sales_pdf(
    tenant: ReportingReadContext,
    service: ReportingServiceDep,
) -> Response:
    data = await service.build_sales_report(empresa_id=tenant.empresa_id)
    return _pdf_response(data, report="sales")


@router.get(
    "/sales/excel",
    summary="Descargar reporte de ventas en Excel",
    response_class=Response,
)
async def sales_excel(
    tenant: ReportingReadContext,
    service: ReportingServiceDep,
) -> Response:
    data = await service.build_sales_report(empresa_id=tenant.empresa_id)
    return _xlsx_response(data, report="sales")


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------
@router.get(
    "/inventory/pdf",
    summary="Descargar reporte de inventario en PDF",
    response_class=Response,
)
async def inventory_pdf(
    tenant: ReportingReadContext,
    service: ReportingServiceDep,
) -> Response:
    data = await service.build_inventory_report(empresa_id=tenant.empresa_id)
    return _pdf_response(data, report="inventory")


@router.get(
    "/inventory/excel",
    summary="Descargar reporte de inventario en Excel",
    response_class=Response,
)
async def inventory_excel(
    tenant: ReportingReadContext,
    service: ReportingServiceDep,
) -> Response:
    data = await service.build_inventory_report(empresa_id=tenant.empresa_id)
    return _xlsx_response(data, report="inventory")


__all__ = ["router"]
