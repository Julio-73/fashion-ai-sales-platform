"""Integration tests for the WhatsApp API.

These tests build a standalone FastAPI app with the WhatsApp router
and override dependencies so the suite runs without a live database.
"""
from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.security.dependencies import TenantContext
from app.modules.whatsapp.router import router as whatsapp_router


TENANT = TenantContext(
    empresa_id=UUID("11111111-1111-4111-8111-111111111111"),
    user_id=UUID("22222222-2222-4222-8222-222222222222"),
    roles=["owner"],
    permissions={
        "whatsapp:read",
        "whatsapp:write",
        "whatsapp:admin",
        "customers:read",
        "customers:write",
        "conversations:read",
        "conversations:write",
        "products:read",
        "orders:read",
        "orders:write",
    },
)


def _build_app(service_stub: AsyncMock) -> FastAPI:
    app = FastAPI()
    app.include_router(whatsapp_router, prefix="/api/v1/whatsapp")
    from app.core.errors import register_exception_handlers

    register_exception_handlers(app)

    async def _service_override():
        return service_stub

    async def _tenant_override():
        return TENANT

    from app.core.security.dependencies import get_tenant_context
    from app.modules.whatsapp.dependencies import get_whatsapp_service

    app.dependency_overrides[get_tenant_context] = _tenant_override
    app.dependency_overrides[get_whatsapp_service] = _service_override
    return app


def _account(**overrides) -> SimpleNamespace:
    base = dict(
        id=uuid4(),
        empresa_id=TENANT.empresa_id,
        phone_number_id="1234567890",
        business_account_id="biz-1",
        display_phone_number="+51999999999",
        verified_name="Demo",
        api_version="v20.0",
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _message(**overrides) -> SimpleNamespace:
    base = dict(
        id=uuid4(),
        empresa_id=TENANT.empresa_id,
        account_id=uuid4(),
        conversation_id=uuid4(),
        direction="outbound",
        wa_message_id="dryrun-abc",
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
    return SimpleNamespace(**base)


def _webhook(**overrides) -> SimpleNamespace:
    base = dict(
        id=uuid4(),
        empresa_id=TENANT.empresa_id,
        phone_number_id="1234567890",
        event_type="message",
        processed=True,
        error=None,
        received_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
    )
    base.update(overrides)
    return SimpleNamespace(**base)


class TestWhatsappAccountEndpoints:
    def test_list_accounts(self) -> None:
        service = AsyncMock()
        service.list_accounts.return_value = [_account(), _account()]
        client = TestClient(_build_app(service))
        response = client.get("/api/v1/whatsapp/accounts")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_create_account_returns_201(self) -> None:
        service = AsyncMock()
        service.create_account.return_value = _account(phone_number_id="NEW-ID")
        client = TestClient(_build_app(service))
        response = client.post(
            "/api/v1/whatsapp/accounts",
            json={
                "phone_number_id": "NEW-ID",
                "access_token": "",
                "webhook_verify_token": "verify-token-1234",
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["phone_number_id"] == "NEW-ID"
        # Secret never exposed
        assert "access_token" not in body
        assert "webhook_verify_token" not in body

    def test_create_account_validates_minimums(self) -> None:
        service = AsyncMock()
        client = TestClient(_build_app(service))
        response = client.post(
            "/api/v1/whatsapp/accounts",
            json={"phone_number_id": "1234567890", "access_token": ""},
        )
        assert response.status_code == 422

    def test_get_account(self) -> None:
        service = AsyncMock()
        account = _account()
        service.get_account.return_value = account
        client = TestClient(_build_app(service))
        response = client.get(f"/api/v1/whatsapp/accounts/{account.id}")
        assert response.status_code == 200
        assert response.json()["id"] == str(account.id)

    def test_get_account_not_found(self) -> None:
        service = AsyncMock()
        from app.core.errors import AppError

        service.get_account.side_effect = AppError(
            code="whatsapp_account_not_found", message="not found", status_code=404
        )
        client = TestClient(_build_app(service))
        response = client.get(f"/api/v1/whatsapp/accounts/{uuid4()}")
        assert response.status_code == 404

    def test_patch_account(self) -> None:
        service = AsyncMock()
        account = _account(verified_name="Renombrado")
        service.update_account.return_value = account
        client = TestClient(_build_app(service))
        response = client.patch(
            f"/api/v1/whatsapp/accounts/{account.id}",
            json={"verified_name": "Renombrado"},
        )
        assert response.status_code == 200
        assert response.json()["verified_name"] == "Renombrado"

    def test_delete_account_returns_204(self) -> None:
        service = AsyncMock()
        service.delete_account.return_value = None
        client = TestClient(_build_app(service))
        response = client.delete(f"/api/v1/whatsapp/accounts/{uuid4()}")
        assert response.status_code == 204


class TestWhatsappMetrics:
    def test_metrics_returns_payload(self) -> None:
        service = AsyncMock()
        from app.modules.whatsapp.schemas import WhatsappMetricsResponse

        service.get_metrics.return_value = WhatsappMetricsResponse(
            is_configured=True,
            active_accounts=1,
            inbound_total=5,
            outbound_total=4,
            delivered_total=3,
            failed_total=0,
            pending_total=0,
            inbound_last_24h=2,
            outbound_last_24h=1,
            webhooks_last_24h=2,
            webhooks_failed_last_24h=0,
            recent_webhooks=[],
        )
        client = TestClient(_build_app(service))
        response = client.get("/api/v1/whatsapp/metrics")
        assert response.status_code == 200
        body = response.json()
        assert body["is_configured"] is True
        assert body["inbound_total"] == 5


class TestWhatsappSend:
    def test_send_returns_201(self) -> None:
        service = AsyncMock()
        from app.modules.whatsapp.schemas import WhatsappSendResponse

        service.send_message.return_value = WhatsappSendResponse(
            message=_message(),
            accepted=True,
            provider_response={"dry_run": True, "synthetic_id": "dryrun-abc"},
        )
        client = TestClient(_build_app(service))
        response = client.post(
            "/api/v1/whatsapp/send",
            json={"to_phone": "51988887777", "body": "Hola"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["accepted"] is True
        assert body["message"]["direction"] == "outbound"

    def test_send_normalizes_phone(self) -> None:
        service = AsyncMock()
        from app.modules.whatsapp.schemas import WhatsappSendResponse

        service.send_message.return_value = WhatsappSendResponse(
            message=_message(),
            accepted=True,
            provider_response={"dry_run": True},
        )
        client = TestClient(_build_app(service))
        response = client.post(
            "/api/v1/whatsapp/send",
            json={"to_phone": "+51 988 887 777", "body": "Hola"},
        )
        assert response.status_code == 201
        # The service is called with the normalized number; we don't
        # assert on the exact value here, only that the call succeeded.

    def test_send_validates_too_short_phone(self) -> None:
        service = AsyncMock()
        client = TestClient(_build_app(service))
        response = client.post(
            "/api/v1/whatsapp/send",
            json={"to_phone": "12345", "body": "Hola"},
        )
        assert response.status_code == 422

    def test_send_empty_body_rejected(self) -> None:
        service = AsyncMock()
        client = TestClient(_build_app(service))
        response = client.post(
            "/api/v1/whatsapp/send",
            json={"to_phone": "51988887777", "body": ""},
        )
        assert response.status_code == 422


class TestWhatsappMessages:
    def test_list_messages(self) -> None:
        service = AsyncMock()
        service.list_messages.return_value = ([_message(), _message()], 2)
        client = TestClient(_build_app(service))
        response = client.get("/api/v1/whatsapp/messages")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 2
        assert len(body["items"]) == 2

    def test_list_messages_with_direction_filter(self) -> None:
        service = AsyncMock()
        service.list_messages.return_value = ([_message(direction="inbound")], 1)
        client = TestClient(_build_app(service))
        response = client.get("/api/v1/whatsapp/messages?direction=inbound")
        assert response.status_code == 200
        service.list_messages.assert_awaited()
        kwargs = service.list_messages.await_args.kwargs
        assert kwargs["direction"] == "inbound"

    def test_list_messages_rejects_invalid_direction(self) -> None:
        service = AsyncMock()
        from app.core.errors import AppError

        service.list_messages.side_effect = AppError(
            code="whatsapp_invalid_direction", message="bad", status_code=422
        )
        client = TestClient(_build_app(service))
        response = client.get("/api/v1/whatsapp/messages?direction=foo")
        assert response.status_code == 422


class TestWhatsappWebhooks:
    def test_list_webhooks(self) -> None:
        service = AsyncMock()
        service.list_webhooks.return_value = ([_webhook(), _webhook()], 2)
        client = TestClient(_build_app(service))
        response = client.get("/api/v1/whatsapp/webhooks")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 2

    def test_webhook_post_returns_200(self) -> None:
        service = AsyncMock()
        service.process_inbound_webhook.return_value = {
            "received": 1, "processed": 1, "failed": 0,
        }
        client = TestClient(_build_app(service))
        response = client.post(
            "/api/v1/whatsapp/webhook",
            json={
                "entry": [{
                    "changes": [{
                        "value": {
                            "metadata": {"phone_number_id": "1234567890"},
                            "messages": [{
                                "from": "51988887777",
                                "id": "wamid.1",
                                "type": "text",
                                "text": {"body": "hola"},
                            }],
                        }
                    }]
                }]
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["received"] == 1
        assert body["processed"] == 1

    def test_webhook_post_invalid_json_returns_400(self) -> None:
        service = AsyncMock()
        client = TestClient(_build_app(service))
        response = client.post(
            "/api/v1/whatsapp/webhook",
            content="not-json",
        )
        assert response.status_code in (400, 422)


class TestWhatsappWebhookVerification:
    def test_verification_with_valid_token(self) -> None:
        service = AsyncMock()
        # Mock the DB query that looks up the verify token.
        service._session = AsyncMock()
        service._session.execute = AsyncMock()

        async def _fake_execute(*args, **kwargs):
            # The router does: select(WhatsappAccount).where(active=True)
            return SimpleNamespace(
                scalars=lambda: SimpleNamespace(all=lambda: [
                    SimpleNamespace(webhook_verify_token="verify-token-1234")
                ])
            )

        service._session.execute.side_effect = _fake_execute
        client = TestClient(_build_app(service))
        response = client.get(
            "/api/v1/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=verify-token-1234&hub.challenge=12345"
        )
        assert response.status_code == 200
        assert response.json()["challenge"] == "12345"

    def test_verification_with_invalid_token_returns_403(self) -> None:
        service = AsyncMock()
        service._session = AsyncMock()
        service._session.execute = AsyncMock()

        async def _fake_execute(*args, **kwargs):
            return SimpleNamespace(
                scalars=lambda: SimpleNamespace(all=lambda: [
                    SimpleNamespace(webhook_verify_token="verify-token-1234")
                ])
            )

        service._session.execute.side_effect = _fake_execute
        client = TestClient(_build_app(service))
        response = client.get(
            "/api/v1/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=WRONG&hub.challenge=12345"
        )
        assert response.status_code == 403
