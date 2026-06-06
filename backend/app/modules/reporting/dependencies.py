"""FastAPI auth dependencies for the Reporting module.

Uses the standard ``require_permission`` factory and ``TenantContext``
from the platform. The permission is ``reports:read`` which is granted
to owner / admin / sales_agent / analyst in
``app.core.security.permissions``.

The permission-checking callables are bound to module-level names (not
anonymous closures produced by ``require_permission(...)``) so tests
can target them via ``app.dependency_overrides[...]``.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.dependencies import TenantContext
from app.core.security.permissions import require_permission
from app.database.session import get_db_session
from app.modules.reporting.service import ReportingService


# ---------------------------------------------------------------------------
# Permission-gated dependencies (named callables — override-friendly)
# ---------------------------------------------------------------------------
reporting_read_dep = require_permission("reports:read")


# ---------------------------------------------------------------------------
# Annotated aliases
# ---------------------------------------------------------------------------
ReportingReadContext = Annotated[
    TenantContext, Depends(reporting_read_dep)
]
DB = Annotated[AsyncSession, Depends(get_db_session)]


# ---------------------------------------------------------------------------
# Service factory
# ---------------------------------------------------------------------------
def get_reporting_service(db: DB) -> ReportingService:
    """Build a ``ReportingService`` bound to the request session."""
    return ReportingService(session=db)


ReportingServiceDep = Annotated[
    ReportingService, Depends(get_reporting_service)
]


__all__ = [
    "DB",
    "ReportingReadContext",
    "ReportingServiceDep",
    "get_reporting_service",
    "reporting_read_dep",
]
