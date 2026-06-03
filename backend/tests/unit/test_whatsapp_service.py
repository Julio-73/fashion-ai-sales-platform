"""Unit tests for the WhatsApp service with mocked collaborators."""
from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from app.core.errors import AppError
from app.core.security.dependencies import TenantContext
from app.modules.whatsapp.cloud_api import (
    WhatsappCloudAPIError,
    WhatsappCloudClient,
)
from app.modules.whatsapp.models import (
    WhatsappAccount,
    WhatsappMessage,
    WhatsappWebhook,
)
from app.modules.whatsapp.schemas import (
    WhatsappAccountCreateRequest,
    WhatsappAccountUpdateRequest,
    WhatsappSendRequest,
)
from app.modules.whatsapp.service import WhatsappService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tenant() -> TenantContext:
    return TenantContext(
        empresa_id=UUID("11111111-1111-4111-8111-111111111111"),
        user_id=UUID("22222222-2222-4222-8222-222222222222"),
        roles=["owner"],
        permissions={"whatsapp:read", "whatsapp:write", "whatsapp:admin"},
    )


@pytest.fixture
def account_id() -> UUID:
    return UUID("33333333-3333-4333-8333-333333333333")


def _account(**overrides) -> MagicMock:
    base = dict(
        id=uuid4(),
        empresa_id=UUID("11111111-1111-4111-8111-111111111111"),
        phone_number_id="1234567890",
        business_account_id="biz-1",
        display_phone_number="+51999999999",
        verified_name="Demo",
        access_token="",
        webhook_verify_token="verify-token",
        api_version="v20.0",
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    base.update(overrides)
    return MagicMock(spec=WhatsappAccount, **base)


def _message(**overrides) -> MagicMock:
    base = dict(
        id=uuid4(),
        empresa_id=UUID("11111111-1111-4111-8111-111111111111"),
        account_id=uuid4(),
        conversation_id=uuid4(),
        direction="outbound",
        wa_message_id=None,
        from_phone="+51999999999",
        to_phone="51988887777",
        body="hola",
        message_type="text",
        status="sent",
        error=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    base.update(overrides)
    return MagicMock(spec=WhatsappMessage, **base)


def _webhook(**overrides) -> MagicMock:
    base = dict(
        id=uuid4(),
        empresa_id=UUID("11111111-1111-4111-8111-111111111111"),
        phone_number_id="1234567890",
        event_type="message",
        payload={},
        processed=True,
        error=None,
        received_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
    )
    base.update(overrides)
    return MagicMock(spec=WhatsappWebhook, **base)


def _build_service(
    *,
    cloud: WhatsappCloudClient | None = None,
) -> tuple[WhatsappService, dict[str, AsyncMock]]:
    session = MagicMock()
    account_repo = MagicMock()
    webhook_repo = MagicMock()
    message_repo = MagicMock()

    account_repo.create = AsyncMock()
    account_repo.get_by_id = AsyncMock()
    account_repo.get_by_phone_number_id = AsyncMock()
    account_repo.list_active = AsyncMock()
    account_repo.list_all = AsyncMock()
    account_repo.update = AsyncMock()
    account_repo.soft_delete = AsyncMock()
    account_repo.commit = AsyncMock()
    account_repo.rollback = AsyncMock()

    webhook_repo.record = AsyncMock()
    webhook_repo.list_recent = AsyncMock()
    webhook_repo.mark_processed = AsyncMock()
    webhook_repo.count_since = AsyncMock()
    webhook_repo.commit = AsyncMock()

    message_repo.create = AsyncMock()
    message_repo.update_status = AsyncMock()
    message_repo.list = AsyncMock()
    message_repo.counts_since = AsyncMock()
    message_repo.commit = AsyncMock()

    service = WhatsappService(
        session=session,
        account_repo=account_repo,
        webhook_repo=webhook_repo,
        message_repo=message_repo,
        cloud_client=cloud or WhatsappCloudClient(force_dry_run=True),
    )
    return service, {
        "session": session,
        "account": account_repo,
        "webhook": webhook_repo,
        "message": message_repo,
    }


# ---------------------------------------------------------------------------
# Account CRUD
# ---------------------------------------------------------------------------


class TestCreateAccount:
    @pytest.mark.asyncio
    async def test_returns_response(self, tenant) -> None:
        service, repos = _build_service()
        repos["account"].create.return_value = _account()
        payload = WhatsappAccountCreateRequest(
            phone_number_id="1234567890",
            access_token="",
            webhook_verify_token="verify-token",
        )
        result = await service.create_account(tenant=tenant, payload=payload)
        assert result.phone_number_id == "1234567890"
        repos["account"].commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_rollback_on_error(self, tenant) -> None:
        service, repos = _build_service()
        repos["account"].create.side_effect = RuntimeError("boom")
        payload = WhatsappAccountCreateRequest(
            phone_number_id="1234567890",
            access_token="",
            webhook_verify_token="verify-token",
        )
        with pytest.raises(AppError) as exc:
            await service.create_account(tenant=tenant, payload=payload)
        assert exc.value.code == "whatsapp_account_conflict"
        repos["account"].rollback.assert_awaited_once()


class TestUpdateAccount:
    @pytest.mark.asyncio
    async def test_updates_existing(self, tenant, account_id) -> None:
        service, repos = _build_service()
        repos["account"].get_by_id.return_value = _account(id=account_id)
        repos["account"].update.return_value = _account(
            id=account_id, verified_name="Updated"
        )
        payload = WhatsappAccountUpdateRequest(verified_name="Updated")
        result = await service.update_account(
            tenant=tenant, account_id=account_id, payload=payload
        )
        assert result.verified_name == "Updated"

    @pytest.mark.asyncio
    async def test_missing_account_raises_404(self, tenant, account_id) -> None:
        service, repos = _build_service()
        repos["account"].get_by_id.return_value = None
        with pytest.raises(AppError) as exc:
            await service.update_account(
                tenant=tenant, account_id=account_id, payload=WhatsappAccountUpdateRequest()
            )
        assert exc.value.code == "whatsapp_account_not_found"


class TestListAccounts:
    @pytest.mark.asyncio
    async def test_returns_responses(self, tenant) -> None:
        service, repos = _build_service()
        repos["account"].list_all.return_value = [_account(), _account()]
        result = await service.list_accounts(tenant=tenant)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# Send (outbound)
# ---------------------------------------------------------------------------


class TestSendMessage:
    @pytest.mark.asyncio
    async def test_dry_run_returns_synthetic_id(self, tenant) -> None:
        service, repos = _build_service()
        repos["account"].list_active.return_value = [_account()]
        repos["message"].create.return_value = _message(status="sent")
        payload = WhatsappSendRequest(to_phone="51988887777", body="Hola")
        result = await service.send_message(tenant=tenant, payload=payload)
        assert result.accepted is True
        assert result.message.status == "sent"
        assert result.provider_response is not None
        assert result.provider_response.get("dry_run") is True
        repos["message"].commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_no_active_account_raises_409(self, tenant) -> None:
        service, repos = _build_service()
        repos["account"].list_active.return_value = []
        payload = WhatsappSendRequest(to_phone="51988887777", body="Hola")
        with pytest.raises(AppError) as exc:
            await service.send_message(tenant=tenant, payload=payload)
        assert exc.value.code == "whatsapp_account_not_configured"

    @pytest.mark.asyncio
    async def test_specific_account_id_used(self, tenant) -> None:
        service, repos = _build_service()
        target = _account(id=uuid4())
        repos["account"].get_by_id.return_value = target
        repos["message"].create.return_value = _message()
        payload = WhatsappSendRequest(
            to_phone="51988887777", body="Hola", account_id=target.id
        )
        await service.send_message(tenant=tenant, payload=payload)
        repos["account"].get_by_id.assert_awaited_with(
            empresa_id=tenant.empresa_id, account_id=target.id
        )

    @pytest.mark.asyncio
    async def test_failed_send_marks_message_failed(self, tenant) -> None:
        cloud = MagicMock(spec=WhatsappCloudClient)
        cloud.send_text_message = AsyncMock(
            side_effect=WhatsappCloudAPIError(status_code=400, body={"error": "x"})
        )
        service, repos = _build_service(cloud=cloud)
        repos["account"].list_active.return_value = [_account()]
        repos["message"].create.return_value = _message(status="failed", error="...")
        payload = WhatsappSendRequest(to_phone="51988887777", body="Hola")
        result = await service.send_message(tenant=tenant, payload=payload)
        assert result.accepted is False
        # message was still created with status=failed
        repos["message"].create.assert_awaited()


# ---------------------------------------------------------------------------
# Webhook processing
# ---------------------------------------------------------------------------


class TestProcessInboundWebhook:
    @pytest.mark.asyncio
    async def test_no_messages_logs_event(self) -> None:
        service, repos = _build_service()
        repos["webhook"].record.return_value = _webhook()
        summary = await service.process_inbound_webhook(
            payload={"entry": [{"changes": [{"value": {"statuses": [{}]}}]}]}
        )
        assert summary == {"received": 0, "processed": 0, "failed": 0}
        repos["webhook"].mark_processed.assert_awaited()

    @pytest.mark.asyncio
    async def test_unknown_account_marks_error(self) -> None:
        service, repos = _build_service()
        repos["account"].get_by_phone_number_id.return_value = None
        repos["webhook"].record.return_value = _webhook()
        # We bypass _handle_single_inbound to focus on the error path.
        with pytest.raises(AppError) as exc:
            await service._handle_single_inbound(
                phone_number_id="9999999999",
                message={"from": "51988887777", "type": "text", "text": {"body": "x"}},
                contacts=[],
                raw_payload={},
            )
        assert exc.value.code == "whatsapp_account_not_found"
        repos["webhook"].mark_processed.assert_awaited()

    @pytest.mark.asyncio
    async def test_unsupported_message_type_is_skipped(self) -> None:
        service, repos = _build_service()
        repos["account"].get_by_phone_number_id.return_value = _account()
        repos["webhook"].record.return_value = _webhook()
        await service._handle_single_inbound(
            phone_number_id="1234567890",
            message={"from": "51988887777", "type": "image", "image": {}},
            contacts=[],
            raw_payload={},
        )
        # mark_processed should be called with an error message
        call_args = repos["webhook"].mark_processed.await_args
        assert "Unsupported" in (call_args.kwargs.get("error") or "")


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


class TestMetrics:
    @pytest.mark.asyncio
    async def test_metrics_aggregates(self, tenant) -> None:
        service, repos = _build_service()
        repos["account"].list_all.return_value = [_account(is_active=True), _account(is_active=False)]
        repos["message"].counts_since.return_value = {
            "inbound": 2,
            "outbound": 3,
            "delivered": 1,
            "failed": 0,
            "pending": 0,
        }
        repos["webhook"].count_since.side_effect = [4, 0]  # 24h, failed_24h
        repos["webhook"].list_recent.return_value = ([_webhook()], 1)
        result = await service.get_metrics(tenant=tenant)
        assert result.is_configured is True
        assert result.active_accounts == 1
        assert result.inbound_total == 2
        assert result.outbound_total == 3
        assert result.webhooks_last_24h == 4
        assert len(result.recent_webhooks) == 1


# ---------------------------------------------------------------------------
# Direct-query helper
# ---------------------------------------------------------------------------


class TestFindOpenConversation:
    @pytest.mark.asyncio
    async def test_helper_compiles_and_executes(self) -> None:
        service, repos = _build_service()
        # Wire a real async execute that returns a None scalar so the
        # helper can complete without touching a real database.
        repos["session"].execute = AsyncMock(
            return_value=SimpleNamespace(
                scalar_one_or_none=lambda: None,
            )
        )
        result = await service._find_open_conversation(
            empresa_id=UUID("11111111-1111-4111-8111-111111111111"),
            cliente_id=uuid4(),
        )
        assert result is None
        repos["session"].execute.assert_awaited()
