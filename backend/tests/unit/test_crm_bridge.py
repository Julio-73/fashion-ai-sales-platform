"""Tests for CrmBridgeService."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from app.core.errors import AppError
from app.modules.customers.models import Cliente
from app.modules.customers.repository import CustomerRepository
from app.services.crm_bridge import CrmBridgeService
from app.services.tag_evaluator import TagEvaluationContext, TagEvaluator
from tests.conftest import TEST_CUSTOMER_ID, TEST_EMPRESA_ID, TEST_CONVERSATION_ID

pytestmark = pytest.mark.asyncio
_now = datetime.now(UTC)


def _make_cliente(**kw) -> MagicMock:
    defaults = dict(
        id=TEST_CUSTOMER_ID,
        empresa_id=TEST_EMPRESA_ID,
        full_name="Test Customer",
        email="test@example.com",
        phone=None,
        whatsapp=None,
        instagram_username=None,
        tags=[],
        notes=None,
        lead_status="new",
        source=None,
        assigned_to=None,
        last_interaction_at=None,
        conversation_count=0,
        last_conversation_id=None,
        created_at=_now,
        updated_at=_now,
        deleted_at=None,
    )
    defaults.update(kw)
    instance = MagicMock(spec=Cliente)
    for key, value in defaults.items():
        setattr(instance, key, value)
    return instance


@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.flush = AsyncMock()
    return session


@pytest.fixture
def customer_repository(mock_session: AsyncMock) -> CustomerRepository:
    repo = CustomerRepository(session=mock_session)
    repo.get_by_id = AsyncMock()
    repo._session = mock_session
    return repo


@pytest.fixture
def crm_bridge(customer_repository: CustomerRepository, mock_session: AsyncMock) -> CrmBridgeService:
    return CrmBridgeService(session=mock_session, customer_repository=customer_repository)


class TestSyncAfterMessage:
    async def test_updates_last_interaction_at(
        self, crm_bridge: CrmBridgeService, customer_repository: CustomerRepository
    ):
        cliente = _make_cliente()
        customer_repository.get_by_id = AsyncMock(return_value=cliente)

        before = datetime.now(UTC)
        result = await crm_bridge.sync_after_message(
            empresa_id=TEST_EMPRESA_ID,
            customer_id=TEST_CUSTOMER_ID,
            conversation_id=TEST_CONVERSATION_ID,
            conversation_status="active",
            message_content="Hello",
            message_sender="user",
        )
        after = datetime.now(UTC)

        assert cliente.last_interaction_at is not None
        assert before <= cliente.last_interaction_at.replace(tzinfo=UTC) <= after
        assert not result.should_reactivate

    async def test_updates_last_conversation_id(
        self, crm_bridge: CrmBridgeService, customer_repository: CustomerRepository
    ):
        cliente = _make_cliente()
        customer_repository.get_by_id = AsyncMock(return_value=cliente)
        conv_id = uuid4()

        await crm_bridge.sync_after_message(
            empresa_id=TEST_EMPRESA_ID,
            customer_id=TEST_CUSTOMER_ID,
            conversation_id=conv_id,
            conversation_status="active",
            message_content="Hello",
            message_sender="user",
        )

        assert cliente.last_conversation_id == conv_id

    async def test_reactivates_closed_conversation(
        self, crm_bridge: CrmBridgeService, customer_repository: CustomerRepository
    ):
        cliente = _make_cliente()
        customer_repository.get_by_id = AsyncMock(return_value=cliente)

        result = await crm_bridge.sync_after_message(
            empresa_id=TEST_EMPRESA_ID,
            customer_id=TEST_CUSTOMER_ID,
            conversation_id=TEST_CONVERSATION_ID,
            conversation_status="closed",
            message_content="Hello again",
            message_sender="user",
        )

        assert result.should_reactivate

    async def test_does_not_reactivate_active_conversation(
        self, crm_bridge: CrmBridgeService, customer_repository: CustomerRepository
    ):
        cliente = _make_cliente()
        customer_repository.get_by_id = AsyncMock(return_value=cliente)

        result = await crm_bridge.sync_after_message(
            empresa_id=TEST_EMPRESA_ID,
            customer_id=TEST_CUSTOMER_ID,
            conversation_id=TEST_CONVERSATION_ID,
            conversation_status="active",
            message_content="Hello",
            message_sender="user",
        )

        assert not result.should_reactivate

    async def test_skips_when_customer_not_found(
        self, crm_bridge: CrmBridgeService, customer_repository: CustomerRepository
    ):
        customer_repository.get_by_id = AsyncMock(return_value=None)

        result = await crm_bridge.sync_after_message(
            empresa_id=TEST_EMPRESA_ID,
            customer_id=uuid4(),
            conversation_id=TEST_CONVERSATION_ID,
            conversation_status="active",
            message_content="Hello",
            message_sender="user",
        )

        assert not result.should_reactivate

    async def test_invokes_tag_evaluator(
        self, customer_repository: CustomerRepository, mock_session: AsyncMock
    ):
        cliente = _make_cliente(tags=["vip"])
        customer_repository.get_by_id = AsyncMock(return_value=cliente)

        mock_evaluator = MagicMock(spec=TagEvaluator)
        mock_evaluator.evaluate = AsyncMock(return_value=["interested"])

        bridge = CrmBridgeService(
            session=mock_session,
            customer_repository=customer_repository,
            tag_evaluator=mock_evaluator,
        )

        await bridge.sync_after_message(
            empresa_id=TEST_EMPRESA_ID,
            customer_id=TEST_CUSTOMER_ID,
            conversation_id=TEST_CONVERSATION_ID,
            conversation_status="active",
            message_content="I want to buy",
            message_sender="user",
        )

        mock_evaluator.evaluate.assert_awaited_once()
        call_args: TagEvaluationContext = mock_evaluator.evaluate.await_args[0][0]
        assert call_args.customer_id == TEST_CUSTOMER_ID
        assert call_args.message_content == "I want to buy"
        assert "vip" in call_args.existing_tags

    async def test_appends_suggested_tags(
        self, customer_repository: CustomerRepository, mock_session: AsyncMock
    ):
        cliente = _make_cliente(tags=["vip"])
        customer_repository.get_by_id = AsyncMock(return_value=cliente)

        mock_evaluator = MagicMock(spec=TagEvaluator)
        mock_evaluator.evaluate = AsyncMock(return_value=["interested", "negotiation"])

        bridge = CrmBridgeService(
            session=mock_session,
            customer_repository=customer_repository,
            tag_evaluator=mock_evaluator,
        )

        await bridge.sync_after_message(
            empresa_id=TEST_EMPRESA_ID,
            customer_id=TEST_CUSTOMER_ID,
            conversation_id=TEST_CONVERSATION_ID,
            conversation_status="active",
            message_content="Hello",
            message_sender="user",
        )

        assert "interested" in cliente.tags
        assert "negotiation" in cliente.tags
        assert "vip" in cliente.tags

    async def test_multi_tenant_isolation(
        self, crm_bridge: CrmBridgeService, customer_repository: CustomerRepository
    ):
        cliente = _make_cliente(empresa_id=TEST_EMPRESA_ID)
        customer_repository.get_by_id = AsyncMock(return_value=None)

        other_empresa = uuid4()
        await crm_bridge.sync_after_message(
            empresa_id=other_empresa,
            customer_id=TEST_CUSTOMER_ID,
            conversation_id=TEST_CONVERSATION_ID,
            conversation_status="active",
            message_content="Hello",
            message_sender="user",
        )

        customer_repository.get_by_id.assert_called_once_with(
            empresa_id=other_empresa, customer_id=TEST_CUSTOMER_ID
        )


class TestIncrementConversationCount:
    async def test_increments_count(
        self, crm_bridge: CrmBridgeService, customer_repository: CustomerRepository
    ):
        cliente = _make_cliente(conversation_count=3)
        customer_repository.get_by_id = AsyncMock(return_value=cliente)

        await crm_bridge.increment_conversation_count(
            empresa_id=TEST_EMPRESA_ID,
            customer_id=TEST_CUSTOMER_ID,
        )

        assert cliente.conversation_count == 4

    async def test_skips_when_not_found(
        self, crm_bridge: CrmBridgeService, customer_repository: CustomerRepository
    ):
        customer_repository.get_by_id = AsyncMock(return_value=None)

        await crm_bridge.increment_conversation_count(
            empresa_id=TEST_EMPRESA_ID,
            customer_id=uuid4(),
        )


class TestSyncConversationStatus:
    async def test_converted_sets_lead_status_won(
        self, crm_bridge: CrmBridgeService, customer_repository: CustomerRepository
    ):
        cliente = _make_cliente(lead_status="negotiating", tags=["vip"])
        customer_repository.get_by_id = AsyncMock(return_value=cliente)

        await crm_bridge.sync_conversation_status(
            empresa_id=TEST_EMPRESA_ID,
            customer_id=TEST_CUSTOMER_ID,
            conversation_status="converted",
        )

        assert cliente.lead_status == "won"
        assert "won" in cliente.tags
        assert "vip" in cliente.tags

    async def test_converted_does_not_overwrite_existing_won(
        self, crm_bridge: CrmBridgeService, customer_repository: CustomerRepository
    ):
        cliente = _make_cliente(lead_status="won", tags=["won"])
        customer_repository.get_by_id = AsyncMock(return_value=cliente)

        await crm_bridge.sync_conversation_status(
            empresa_id=TEST_EMPRESA_ID,
            customer_id=TEST_CUSTOMER_ID,
            conversation_status="converted",
        )

        assert cliente.lead_status == "won"
        assert cliente.tags == ["won"]

    async def test_non_converted_does_not_change_lead_status(
        self, crm_bridge: CrmBridgeService, customer_repository: CustomerRepository
    ):
        cliente = _make_cliente(lead_status="negotiating", tags=["vip"])
        customer_repository.get_by_id = AsyncMock(return_value=cliente)

        await crm_bridge.sync_conversation_status(
            empresa_id=TEST_EMPRESA_ID,
            customer_id=TEST_CUSTOMER_ID,
            conversation_status="active",
        )

        assert cliente.lead_status == "negotiating"
        assert cliente.tags == ["vip"]

    async def test_skips_when_not_found(
        self, crm_bridge: CrmBridgeService, customer_repository: CustomerRepository
    ):
        customer_repository.get_by_id = AsyncMock(return_value=None)

        await crm_bridge.sync_conversation_status(
            empresa_id=TEST_EMPRESA_ID,
            customer_id=uuid4(),
            conversation_status="converted",
        )


class TestIntegrationWithConversationService:
    async def test_add_message_triggers_crm_sync(
        self, conversation_core_service, conversation_core_repository,
        tenant_context, mock_session, customer_repository
    ):
        from app.services.crm_bridge import CrmBridgeService
        from app.conversations.schemas import MessageCoreCreateRequest
        from app.conversations.models import ConversationCore, MessageCore
        from tests.conftest import TEST_CONVERSATION_ID

        cliente = _make_cliente(empresa_id=tenant_context.empresa_id)
        customer_repository.get_by_id = AsyncMock(return_value=cliente)
        customer_repository._session = mock_session

        crm_bridge = CrmBridgeService(
            session=mock_session,
            customer_repository=customer_repository,
        )

        service = conversation_core_service.__class__(
            repository=conversation_core_repository,
            crm_bridge=crm_bridge,
        )

        mock_c = MagicMock(spec=ConversationCore)
        mock_c.id = TEST_CONVERSATION_ID
        mock_c.empresa_id = tenant_context.empresa_id
        mock_c.customer_id = TEST_CUSTOMER_ID
        mock_c.status = "active"
        mock_c.last_message = None

        mock_m = MagicMock(spec=MessageCore)
        mock_m.id = uuid4()
        mock_m.empresa_id = tenant_context.empresa_id
        mock_m.conversation_id = TEST_CONVERSATION_ID
        mock_m.sender = "user"
        mock_m.content = "Hello"
        mock_m.created_at = _now
        mock_m.updated_at = _now

        conversation_core_repository.get_conversation_by_id = AsyncMock(return_value=mock_c)
        conversation_core_repository.add_message = AsyncMock(return_value=mock_m)
        conversation_core_repository.update_last_message = AsyncMock()
        conversation_core_repository.commit = AsyncMock()

        result = await service.add_message(
            tenant=tenant_context,
            conversation_id=TEST_CONVERSATION_ID,
            payload=MessageCoreCreateRequest(sender="user", content="Hello"),
        )

        assert result.content == "Hello"
        assert cliente.last_interaction_at is not None
        assert cliente.last_conversation_id == TEST_CONVERSATION_ID
