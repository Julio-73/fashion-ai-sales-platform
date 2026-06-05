"""FastAPI auth dependencies for the pipeline module.

Re-uses the existing ``require_permission`` factory from
``app.core.security.permissions`` and the standard ``TenantContext``.

The permission-checking callables are bound to module-level names (not
anonymous closures produced by ``require_permission(...)``) so tests
can target them via ``app.dependency_overrides[...]`` — FastAPI's
override system matches on the callable reference, not on a
``TypeAlias``.

Production behaviour is identical to the previous implementation.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.dependencies import TenantContext
from app.core.security.permissions import require_permission
from app.database.session import get_db_session


# ---------------------------------------------------------------------------
# Permission-gated dependencies (named callables — override-friendly)
# ---------------------------------------------------------------------------
pipeline_read_dep = require_permission("pipeline:read")
pipeline_write_dep = require_permission("pipeline:write")
pipeline_metrics_dep = require_permission("pipeline:metrics")


# ---------------------------------------------------------------------------
# Annotated aliases (preserved for backwards compatibility with imports)
# ---------------------------------------------------------------------------
PipelineReadContext = Annotated[TenantContext, Depends(pipeline_read_dep)]
PipelineWriteContext = Annotated[TenantContext, Depends(pipeline_write_dep)]
PipelineMetricsContext = Annotated[TenantContext, Depends(pipeline_metrics_dep)]
DB = Annotated[AsyncSession, Depends(get_db_session)]


__all__ = [
    "PipelineReadContext",
    "PipelineWriteContext",
    "PipelineMetricsContext",
    "DB",
    "pipeline_read_dep",
    "pipeline_write_dep",
    "pipeline_metrics_dep",
]
