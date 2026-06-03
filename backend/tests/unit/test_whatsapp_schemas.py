"""Unit tests for the WhatsApp module schemas."""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.modules.whatsapp.schemas import (
    WhatsappAccountCreateRequest,
    WhatsappAccountResponse,
    WhatsappAccountUpdateRequest,
    WhatsappMessageListResponse,
    WhatsappMessageResponse,
    WhatsappMetricsResponse,
    WhatsappSendRequest,
    WhatsappWebhookListResponse,
    WhatsappWebhookResponse,
)


class TestAccountCreateRequest:
    def test_minimum_valid_payload(self) -> None:
        payload = WhatsappAccountCreateRequest(
            phone_number_id="1234567890",
            access_token="",
            webhook_verify_token="verify-token-1234",
        )
        assert payload.phone_number_id == "1234567890"
        assert payload.api_version == "v20.0"
        assert payload.is_active is True

    def test_phone_number_id_required(self) -> None:
        with pytest.raises(ValueError):
            WhatsappAccountCreateRequest(
                phone_number_id="",
                access_token="",
                webhook_verify_token="verify-token-1234",
            )

    def test_webhook_verify_token_min_length(self) -> None:
        with pytest.raises(ValueError):
            WhatsappAccountCreateRequest(
                phone_number_id="1234567890",
                access_token="",
                webhook_verify_token="abc",
            )

    def test_access_token_can_be_empty_for_dry_run(self) -> None:
        payload = WhatsappAccountCreateRequest(
            phone_number_id="1234567890",
            access_token="",
            webhook_verify_token="verify-token-1234",
        )
        assert payload.access_token == ""

    def test_phone_number_id_too_long(self) -> None:
        with pytest.raises(ValueError):
            WhatsappAccountCreateRequest(
                phone_number_id="x" * 65,
                access_token="",
                webhook_verify_token="verify-token-1234",
            )


class TestAccountUpdateRequest:
    def test_partial_update_only_verified_name(self) -> None:
        payload = WhatsappAccountUpdateRequest(verified_name="Mi Empresa")
        assert payload.verified_name == "Mi Empresa"
        assert payload.access_token is None
        assert payload.is_active is None

    def test_empty_payload_is_valid(self) -> None:
        payload = WhatsappAccountUpdateRequest()
        assert payload.verified_name is None
        assert payload.is_active is None


class TestAccountResponseSerialization:
    def test_response_excludes_secrets(self) -> None:
        """The response model should never include access_token or webhook_verify_token."""
        response = WhatsappAccountResponse(
            id=uuid4(),
            empresa_id=uuid4(),
            phone_number_id="1234567890",
            business_account_id=None,
            display_phone_number="+51999999999",
            verified_name=None,
            api_version="v20.0",
            is_active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        dumped = response.model_dump()
        assert "access_token" not in dumped
        assert "webhook_verify_token" not in dumped
        assert dumped["phone_number_id"] == "1234567890"


class TestSendRequest:
    def test_phone_is_normalized_to_digits(self) -> None:
        payload = WhatsappSendRequest(to_phone="+51 988 887 777", body="Hola")
        assert payload.to_phone == "51988887777"

    def test_phone_with_plus_prefix_preserved(self) -> None:
        # After normalization we keep only digits
        payload = WhatsappSendRequest(to_phone="+51988887777", body="Hola")
        assert payload.to_phone == "51988887777"

    def test_phone_too_short_rejected(self) -> None:
        with pytest.raises(ValueError):
            WhatsappSendRequest(to_phone="12345", body="Hola")

    def test_empty_body_rejected(self) -> None:
        with pytest.raises(ValueError):
            WhatsappSendRequest(to_phone="51988887777", body="")

    def test_long_body_rejected(self) -> None:
        with pytest.raises(ValueError):
            WhatsappSendRequest(to_phone="51988887777", body="x" * 5000)


class TestMetricsResponse:
    def test_full_payload(self) -> None:
        payload = WhatsappMetricsResponse(
            is_configured=True,
            active_accounts=1,
            inbound_total=10,
            outbound_total=8,
            delivered_total=7,
            failed_total=1,
            pending_total=0,
            inbound_last_24h=3,
            outbound_last_24h=2,
            webhooks_last_24h=4,
            webhooks_failed_last_24h=0,
            recent_webhooks=[],
        )
        assert payload.is_configured is True
        assert payload.inbound_total == 10
        assert payload.recent_webhooks == []


class TestListResponses:
    def test_message_list_response_envelope(self) -> None:
        payload = WhatsappMessageListResponse(
            items=[],
            total=0,
            limit=25,
            offset=0,
        )
        assert payload.items == []
        assert payload.total == 0

    def test_webhook_list_response_envelope(self) -> None:
        payload = WhatsappWebhookListResponse(
            items=[],
            total=0,
            limit=25,
            offset=0,
        )
        assert payload.total == 0


class TestMessageResponse:
    def test_message_response_round_trip(self) -> None:
        msg = WhatsappMessageResponse(
            id=uuid4(),
            empresa_id=uuid4(),
            account_id=uuid4(),
            conversation_id=uuid4(),
            direction="inbound",
            wa_message_id="wamid.abc",
            from_phone="51988887777",
            to_phone="+51999999999",
            body="Hola",
            message_type="text",
            status="delivered",
            error=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        dumped = msg.model_dump()
        assert dumped["direction"] == "inbound"
        assert dumped["body"] == "Hola"


class TestWebhookResponse:
    def test_webhook_response_with_error(self) -> None:
        wh = WhatsappWebhookResponse(
            id=uuid4(),
            empresa_id=uuid4(),
            phone_number_id="1234567890",
            event_type="message",
            processed=False,
            error="No active account",
            received_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
        )
        assert wh.error == "No active account"
        assert wh.processed is False
