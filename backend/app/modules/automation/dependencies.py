"""FastAPI auth dependencies for the automation module.

The new ``automation:read`` and ``automation:write`` permissions are
resolved by the standard ``require_permission`` factory. We add the
new keys to every role that already had ``pipeline:metrics`` (which
implies access to commercial analytics) so existing users keep a
working dashboard.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.dependencies import TenantContext
from app.core.security.permissions import require_permission
from app.database.session import get_db_session


automation_read_dep = require_permission("automation:read")
automation_write_dep = require_permission("automation:write")


AutomationReadContext = Annotated[TenantContext, Depends(automation_read_dep)]
AutomationWriteContext = Annotated[TenantContext, Depends(automation_write_dep)]
DB = Annotated[AsyncSession, Depends(get_db_session)]


__all__ = [
    "AutomationReadContext",
    "AutomationWriteContext",
    "DB",
    "automation_read_dep",
    "automation_write_dep",
]
