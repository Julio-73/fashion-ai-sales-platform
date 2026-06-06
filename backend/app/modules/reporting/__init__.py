"""Reporting Enterprise V1.

Generates executive-grade PDF and XLSX reports by aggregating the
existing read-only repositories (orders, customers, products, pipeline,
inventory). This module is strictly additive: it never mutates any
existing table and never modifies the contracts of any other module.

Endpoints (mounted under ``/api/v1/reporting``):

* ``GET /executive/pdf``     — Executive report (PDF)
* ``GET /executive/excel``   — Executive report (XLSX, multi-sheet)
* ``GET /pipeline/pdf``      — Pipeline report (PDF)
* ``GET /pipeline/excel``    — Pipeline report (XLSX)
* ``GET /crm/pdf``           — CRM / Customer 360 report (PDF)
* ``GET /crm/excel``         — CRM / Customer 360 report (XLSX)
* ``GET /sales/pdf``         — Sales / Orders report (PDF)
* ``GET /sales/excel``       — Sales / Orders report (XLSX)
* ``GET /inventory/pdf``     — Inventory report (PDF)
* ``GET /inventory/excel``   — Inventory report (XLSX)
"""

from app.modules.reporting.dependencies import (
    DB,
    ReportingReadContext,
    ReportingServiceDep,
    get_reporting_service,
    reporting_read_dep,
)
from app.modules.reporting.router import router as reporting_router
from app.modules.reporting.service import ReportingService

__all__ = [
    "DB",
    "ReportingReadContext",
    "ReportingService",
    "ReportingServiceDep",
    "get_reporting_service",
    "reporting_read_dep",
    "reporting_router",
]
