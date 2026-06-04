"""Unit tests for the AdminAuditRepository (action validation + listing)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.modules.admin.models import ADMIN_AUDIT_ACTIONS
from app.modules.admin.repository import AdminAuditRepository


def test_supported_actions_include_required_audit_events() -> None:
    """The 7 actions requested by the spec are all supported."""
    required = {
        "company_created",
        "company_updated",
        "company_suspended",
        "company_activated",
        "company_expired",
        "plan_changed",
        "status_changed",
    }
    assert required.issubset(set(ADMIN_AUDIT_ACTIONS))


@pytest.mark.asyncio
async def test_record_accepts_supported_actions(mock_session: AsyncMock) -> None:
    repo = AdminAuditRepository(session=mock_session)
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    for action in ADMIN_AUDIT_ACTIONS:
        await repo.record(admin_user_id=uuid4(), action=action)


@pytest.mark.asyncio
async def test_record_rejects_unknown_action(mock_session: AsyncMock) -> None:
    repo = AdminAuditRepository(session=mock_session)
    with pytest.raises(ValueError) as exc:
        await repo.record(admin_user_id=uuid4(), action="made_coffee")
    assert "made_coffee" in str(exc.value)


@pytest.mark.asyncio
async def test_list_builds_correct_query(mock_session: AsyncMock) -> None:
    repo = AdminAuditRepository(session=mock_session)
    admin_user_id = uuid4()
    target_empresa_id = uuid4()
    # count + list
    mock_session.execute = AsyncMock(
        side_effect=[
            MagicMock(scalar_one=lambda: 0),
            MagicMock(scalars=lambda: MagicMock(all=lambda: [])),
        ]
    )
    items, total = await repo.list(
        limit=10,
        offset=0,
        action="company_suspended",
        admin_user_id=admin_user_id,
        target_empresa_id=target_empresa_id,
    )
    assert total == 0
    assert items == []
    assert mock_session.execute.await_count == 2
