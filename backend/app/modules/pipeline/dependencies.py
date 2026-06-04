"""FastAPI auth dependencies for the pipeline module.

Re-uses the existing ``require_permission`` factory from
``app.core.security.permissions`` and the standard ``TenantContext``.
"""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.dependencies import TenantContext
from app.core.security.permissions import require_permission
from app.database.session import get_db_session


PipelineReadContext = Annotated[
    TenantContext,
    Depends(require_permission("pipeline:read")),
]
PipelineWriteContext = Annotated[
    TenantContext,
    Depends(require_permission("pipeline:write")),
]
PipelineMetricsContext = Annotated[
    TenantContext,
    Depends(require_permission("pipeline:metrics")),
]
DB = Annotated[AsyncSession, Depends(get_db_session)]


__all__ = [
    "PipelineReadContext",
    "PipelineWriteContext",
    "PipelineMetricsContext",
    "DB",
]
