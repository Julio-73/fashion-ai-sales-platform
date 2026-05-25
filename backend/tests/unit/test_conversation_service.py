"""Tests for ConversationService."""
from __future__ import annotations
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime, timezone
import pytest
from app.core.errors import AppError
from app.modules.conversations.models import Conversation, Message
from app.modules.conversations.schemas import (
    ConversationCreateRequest, ConversationUpdateRequest, MessageCreateRequest,
)
from tests.conftest import TEST_CONVERSATION_ID

pytestmark = pytest.mark.asyncio
_now = datetime.now(timezone.utc)


def _make_conversation(**kw):
    defaults = dict(id=uuid4(), empresa_id=TEST_CONVERSATION_ID, cliente_id=None,
                    asunto="Test", canal="manual", estado="open",
                    deleted_at=None, created_at=_now, updated_at=_now)
    defaults.update(kw)
    return Conversation(**defaults)


def _make_message(**kw):
    defaults = dict(id=uuid4(), empresa_id=TEST_CONVERSATION_ID, conversation_id=TEST_CONVERSATION_ID,
                    role="agent", content="Hello", sender_name=None, extra_data=None,
                    created_at=_now, updated_at=_now)
    defaults.update(kw)
    return Message(**defaults)


class TestCreateConversation:
    async def test_creates_conversation(self, conversation_service, conversation_repository, tenant_context):
        mock_c = _make_conversation(empresa_id=tenant_context.empresa_id)
        conversation_repository.create_conversation = AsyncMock(return_value=mock_c)
        conversation_repository.commit = AsyncMock()
        result = await conversation_service.create_conversation(
            tenant=tenant_context, payload=ConversationCreateRequest(asunto="Test", canal="manual"))
        assert result.canal == "manual"
        assert result.estado == "open"


class TestGetConversation:
    async def test_returns_conversation_with_messages(self, conversation_service, conversation_repository, tenant_context):
        mock_c = _make_conversation(id=TEST_CONVERSATION_ID, empresa_id=tenant_context.empresa_id)
        mock_m = _make_message(empresa_id=tenant_context.empresa_id, conversation_id=TEST_CONVERSATION_ID)
        conversation_repository.get_conversation_by_id = AsyncMock(return_value=mock_c)
        conversation_repository.list_messages = AsyncMock(return_value=([mock_m], 1))
        result = await conversation_service.get_conversation(tenant=tenant_context, conversation_id=TEST_CONVERSATION_ID)
        assert result.id == TEST_CONVERSATION_ID
        assert len(result.messages) == 1

    async def test_not_found_raises_404(self, conversation_service, conversation_repository, tenant_context):
        conversation_repository.get_conversation_by_id = AsyncMock(return_value=None)
        with pytest.raises(AppError) as e:
            await conversation_service.get_conversation(tenant=tenant_context, conversation_id=uuid4())
        assert e.value.status_code == 404


class TestUpdateConversation:
    async def test_updates_conversation(self, conversation_service, conversation_repository, tenant_context):
        mock_c = _make_conversation(empresa_id=tenant_context.empresa_id)
        conversation_repository.get_conversation_by_id = AsyncMock(return_value=mock_c)
        # Make update return the conversation with updated fields set
        async def _update_side_effect(*, conversation, payload):
            for field, value in payload.model_dump(exclude_unset=True).items():
                setattr(conversation, field, value)
            return conversation
        conversation_repository.update_conversation = AsyncMock(side_effect=_update_side_effect)
        conversation_repository.commit = AsyncMock()
        result = await conversation_service.update_conversation(
            tenant=tenant_context, conversation_id=TEST_CONVERSATION_ID,
            payload=ConversationUpdateRequest(estado="closed"))
        assert result.estado == "closed"


class TestAddMessage:
    async def test_adds_message_to_conversation(self, conversation_service, conversation_repository, tenant_context):
        mock_c = _make_conversation(empresa_id=tenant_context.empresa_id)
        mock_m = _make_message(role="agent", content="Hola", empresa_id=tenant_context.empresa_id)
        conversation_repository.get_conversation_by_id = AsyncMock(return_value=mock_c)
        conversation_repository.add_message = AsyncMock(return_value=mock_m)
        conversation_repository.commit = AsyncMock()
        result = await conversation_service.add_message(
            tenant=tenant_context, conversation_id=TEST_CONVERSATION_ID,
            payload=MessageCreateRequest(role="agent", content="Hola"))
        assert result.role == "agent"
