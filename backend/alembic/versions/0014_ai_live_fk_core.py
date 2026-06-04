"""align conversation_ai_* FKs to conversations_core (additive correction)

Revision ID: 0014_ai_live_fk_core
Revises: 0013_admin_enterprise
Create Date: 2026-06-04

C-1 / C-4 of the Enterprise Stability audit.

Background
----------
The ``conversation_ai_states`` and ``conversation_ai_events`` tables were
created in migration 0008 with a foreign key pointing to ``conversations.id``
(the legacy conversations table from module ``app/modules/conversations``).

However, the AI Live runtime code (``app/ai_live/router.py``,
``app/ai_live/services/auto_reply_service.py``) is invoked with
``conversations_core.id`` (the newer core table created in migration 0005,
used by ``app/conversations`` and the ``/conversations-core`` router). This
mismatch caused ``INSERT`` operations into ``conversation_ai_states`` to
fail with ``ForeignKeyViolationError``, returning HTTP 500 on every
AI Live endpoint (state, toggle-ai, toggle-auto-reply, handoff,
analyze-intent) and on the auto-reply branch of
``POST /conversations-core/{id}/messages``.

This migration drops the wrong FK and recreates it pointing to
``conversations_core.id``, restoring the DB-level guarantee that AI Live
state and events can only ever reference existing core conversations.

Both tables were empty at the time of the fix (the only write path was
the broken route, so the broken FK prevented any row from being created).
The ``downgrade`` reverts to ``conversations.id`` for safety; if a future
downgrade is ever executed after rows exist pointing to
``conversations_core``, the DB will raise — that is intentional, as it
mirrors the original (buggy) state.
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "0014_ai_live_fk_core"
down_revision: str | None = "0013_admin_enterprise"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ---- conversation_ai_states.conversation_id ----
    op.drop_constraint(
        "conversation_ai_states_conversation_id_fkey",
        "conversation_ai_states",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_ai_states_conversation_id__convcore",
        "conversation_ai_states",
        "conversations_core",
        ["conversation_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # ---- conversation_ai_events.conversation_id ----
    op.drop_constraint(
        "conversation_ai_events_conversation_id_fkey",
        "conversation_ai_events",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_ai_events_conversation_id__convcore",
        "conversation_ai_events",
        "conversations_core",
        ["conversation_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_ai_events_conversation_id__convcore",
        "conversation_ai_events",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "conversation_ai_events_conversation_id_fkey",
        "conversation_ai_events",
        "conversations",
        ["conversation_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint(
        "fk_ai_states_conversation_id__convcore",
        "conversation_ai_states",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "conversation_ai_states_conversation_id_fkey",
        "conversation_ai_states",
        "conversations",
        ["conversation_id"],
        ["id"],
        ondelete="CASCADE",
    )


__all__ = ["upgrade", "downgrade"]
