"""Tests for ConversationCoreService."""
from __future__ import annotations
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime, timezone
import pytest
from app.conversations.models import ConversationCore, MessageCore
from app.conversations.schemas import (
    ConversationCoreCreateRequest, MessageCoreCreateRequest,
)
from app.core.errors import AppError
from tests.conftest import TEST_CONVERSATION_ID

pytestmark = pytest.mark.asyncio
_now = datetime.now(timezone.utc)


def _make_conversation(**kw):
    defaults = dict(id=uuid4(), empresa_id=TEST_CONVERSATION_ID, customer_id=None,
                    status="active", last_message=None,
                    created_at=_now, updated_at=_now)
    defaults.update(kw)
    return ConversationCore(**defaults)


def _make_message(**kw):
    defaults = dict(id=uuid4(), empresa_id=TEST_CONVERSATION_ID,
                    conversation_id=TEST_CONVERSATION_ID,
                    sender="user", content="Hello",
                    created_at=_now, updated_at=_now)
    defaults.update(kw)
    return MessageCore(**defaults)


class TestCreateConversation:
    async def test_creates_conversation(self, conversation_core_service, conversation_core_repository, tenant_context):
        mock_c = _make_conversation(empresa_id=tenant_context.empresa_id)
        conversation_core_repository.create_conversation = AsyncMock(return_value=mock_c)
        conversation_core_repository.commit = AsyncMock()
        result = await conversation_core_service.create_conversation(
            tenant=tenant_context, payload=ConversationCoreCreateRequest())
        assert result.status == "active"
        assert result.customer_id is None

    async def test_creates_conversation_with_customer(self, conversation_core_service, conversation_core_repository, tenant_context):
        customer_id = uuid4()
        mock_c = _make_conversation(empresa_id=tenant_context.empresa_id, customer_id=customer_id)
        conversation_core_repository.create_conversation = AsyncMock(return_value=mock_c)
        conversation_core_repository.commit = AsyncMock()
        result = await conversation_core_service.create_conversation(
            tenant=tenant_context,
            payload=ConversationCoreCreateRequest(customer_id=customer_id))
        assert result.customer_id == customer_id


class TestGetConversation:
    async def test_returns_conversation_with_messages(self, conversation_core_service, conversation_core_repository, tenant_context):
        mock_c = _make_conversation(id=TEST_CONVERSATION_ID, empresa_id=tenant_context.empresa_id)
        mock_m = _make_message(empresa_id=tenant_context.empresa_id, conversation_id=TEST_CONVERSATION_ID)
        conversation_core_repository.get_conversation_by_id = AsyncMock(return_value=mock_c)
        conversation_core_repository.list_messages = AsyncMock(return_value=([mock_m], 1))
        result = await conversation_core_service.get_conversation(tenant=tenant_context, conversation_id=TEST_CONVERSATION_ID)
        assert result.id == TEST_CONVERSATION_ID
        assert len(result.messages) == 1

    async def test_not_found_raises_404(self, conversation_core_service, conversation_core_repository, tenant_context):
        conversation_core_repository.get_conversation_by_id = AsyncMock(return_value=None)
        with pytest.raises(AppError) as e:
            await conversation_core_service.get_conversation(tenant=tenant_context, conversation_id=uuid4())
        assert e.value.status_code == 404


class TestListConversations:
    async def test_returns_paginated_list(self, conversation_core_service, conversation_core_repository, tenant_context):
        mock_c = _make_conversation(empresa_id=tenant_context.empresa_id)
        conversation_core_repository.list_conversations = AsyncMock(return_value=([mock_c], 1))
        result = await conversation_core_service.list_conversations(
            tenant=tenant_context, limit=25, offset=0, search=None, status=None)
        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].status == "active"

    async def test_filters_by_status(self, conversation_core_service, conversation_core_repository, tenant_context):
        mock_c = _make_conversation(empresa_id=tenant_context.empresa_id, status="closed")
        conversation_core_repository.list_conversations = AsyncMock(return_value=([mock_c], 1))
        result = await conversation_core_service.list_conversations(
            tenant=tenant_context, limit=25, offset=0, search=None, status="closed")
        assert result.total == 1
        assert result.items[0].status == "closed"

    async def test_multi_tenant_isolation(self, conversation_core_service, conversation_core_repository, tenant_context):
        other_empresa_id = uuid4()
        mock_own = _make_conversation(empresa_id=tenant_context.empresa_id)
        mock_other = _make_conversation(empresa_id=other_empresa_id)
        conversation_core_repository.list_conversations = AsyncMock(return_value=([mock_own], 1))
        result = await conversation_core_service.list_conversations(
            tenant=tenant_context, limit=25, offset=0, search=None, status=None)
        assert result.total == 1
        for item in result.items:
            assert item.empresa_id == tenant_context.empresa_id


class TestAddMessage:
    async def test_adds_message_and_updates_last_message(self, conversation_core_service, conversation_core_repository, tenant_context):
        mock_c = _make_conversation(id=TEST_CONVERSATION_ID, empresa_id=tenant_context.empresa_id)
        mock_m = _make_message(sender="user", content="Hello", empresa_id=tenant_context.empresa_id)
        conversation_core_repository.get_conversation_by_id = AsyncMock(return_value=mock_c)
        conversation_core_repository.add_message = AsyncMock(return_value=mock_m)
        conversation_core_repository.update_last_message = AsyncMock()
        conversation_core_repository.commit = AsyncMock()
        result = await conversation_core_service.add_message(
            tenant=tenant_context, conversation_id=TEST_CONVERSATION_ID,
            payload=MessageCoreCreateRequest(sender="user", content="Hello"))
        assert result.sender == "user"
        assert result.content == "Hello"
        conversation_core_repository.update_last_message.assert_called_once_with(
            conversation=mock_c, content="Hello")

    async def test_message_not_found_raises_404(self, conversation_core_service, conversation_core_repository, tenant_context):
        conversation_core_repository.get_conversation_by_id = AsyncMock(return_value=None)
        with pytest.raises(AppError) as e:
            await conversation_core_service.add_message(
                tenant=tenant_context, conversation_id=uuid4(),
                payload=MessageCoreCreateRequest(sender="user", content="Hello"))
        assert e.value.status_code == 404


class TestListMessages:
    async def test_returns_messages_for_conversation(self, conversation_core_service, conversation_core_repository, tenant_context):
        mock_c = _make_conversation(id=TEST_CONVERSATION_ID, empresa_id=tenant_context.empresa_id)
        mock_m = _make_message(empresa_id=tenant_context.empresa_id, conversation_id=TEST_CONVERSATION_ID)
        conversation_core_repository.get_conversation_by_id = AsyncMock(return_value=mock_c)
        conversation_core_repository.list_messages = AsyncMock(return_value=([mock_m], 1))
        result = await conversation_core_service.list_messages(
            tenant=tenant_context, conversation_id=TEST_CONVERSATION_ID, limit=50, offset=0)
        assert result.total == 1
        assert len(result.items) == 1

    async def test_returns_empty_when_no_messages(self, conversation_core_service, conversation_core_repository, tenant_context):
        mock_c = _make_conversation(id=TEST_CONVERSATION_ID, empresa_id=tenant_context.empresa_id)
        conversation_core_repository.get_conversation_by_id = AsyncMock(return_value=mock_c)
        conversation_core_repository.list_messages = AsyncMock(return_value=([], 0))
        result = await conversation_core_service.list_messages(
            tenant=tenant_context, conversation_id=TEST_CONVERSATION_ID, limit=50, offset=0)
        assert result.total == 0
        assert len(result.items) == 0


class TestUpdateConversation:
    async def test_updates_status(self, conversation_core_service, conversation_core_repository, tenant_context):
        mock_c = _make_conversation(empresa_id=tenant_context.empresa_id, status="active")
        conversation_core_repository.get_conversation_by_id = AsyncMock(return_value=mock_c)
        async def _update_side_effect(*, conversation, status):
            conversation.status = status
            return conversation
        conversation_core_repository.update_conversation = AsyncMock(side_effect=_update_side_effect)
        conversation_core_repository.commit = AsyncMock()
        result = await conversation_core_service.update_conversation(
            tenant=tenant_context, conversation_id=TEST_CONVERSATION_ID, status="closed")
        assert result.status == "closed"


class TestDeleteConversation:
    async def test_deletes_conversation(self, conversation_core_service, conversation_core_repository, tenant_context):
        mock_c = _make_conversation(empresa_id=tenant_context.empresa_id)
        conversation_core_repository.get_conversation_by_id = AsyncMock(return_value=mock_c)
        conversation_core_repository.delete_conversation = AsyncMock()
        conversation_core_repository.commit = AsyncMock()
        await conversation_core_service.delete_conversation(tenant=tenant_context, conversation_id=TEST_CONVERSATION_ID)
        conversation_core_repository.delete_conversation.assert_called_once_with(conversation=mock_c)
