"""FastAPI auth dependencies for the executive dashboard module.

Re-uses the standard ``require_permission`` factory and ``TenantContext``
from the platform. The permission used is ``analytics:read`` which is
already granted to every role (owner, admin, sales_agent, analyst) in
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
from app.modules.executive_dashboard.service import ExecutiveDashboardService


# ---------------------------------------------------------------------------
# Permission-gated dependencies (named callables — override-friendly)
# ---------------------------------------------------------------------------
executive_dashboard_read_dep = require_permission("analytics:read")


# ---------------------------------------------------------------------------
# Annotated aliases
# ---------------------------------------------------------------------------
ExecutiveDashboardReadContext = Annotated[
    TenantContext, Depends(executive_dashboard_read_dep)
]
DB = Annotated[AsyncSession, Depends(get_db_session)]


# ---------------------------------------------------------------------------
# Service factory
# ---------------------------------------------------------------------------
def get_executive_dashboard_service(db: DB) -> ExecutiveDashboardService:
    """Build an ``ExecutiveDashboardService`` bound to the request session."""
    return ExecutiveDashboardService(session=db)


ExecutiveDashboardServiceDep = Annotated[
    ExecutiveDashboardService, Depends(get_executive_dashboard_service)
]


__all__ = [
    "ExecutiveDashboardReadContext",
    "ExecutiveDashboardServiceDep",
    "DB",
    "executive_dashboard_read_dep",
    "get_executive_dashboard_service",
]
