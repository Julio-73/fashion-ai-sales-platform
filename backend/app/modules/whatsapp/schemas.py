"""Pydantic schemas for the WhatsApp Business Cloud API integration."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

WhatsappDirection = Literal["inbound", "outbound"]
WhatsappMessageStatus = Literal["pending", "sent", "delivered", "read", "failed"]
WhatsappWebhookEvent = Literal["verification", "message", "status", "unknown"]


# ---------------------------------------------------------------------------
# Account (credentials)
# ---------------------------------------------------------------------------


class WhatsappAccountCreateRequest(BaseModel):
    phone_number_id: str = Field(min_length=4, max_length=64)
    business_account_id: str | None = Field(default=None, max_length=64)
    display_phone_number: str | None = Field(default=None, max_length=32)
    verified_name: str | None = Field(default=None, max_length=160)
    access_token: str = Field(default="", max_length=4096)
    webhook_verify_token: str = Field(min_length=4, max_length=128)
    api_version: str = Field(default="v20.0", max_length=16)
    is_active: bool = True


class WhatsappAccountUpdateRequest(BaseModel):
    business_account_id: str | None = Field(default=None, max_length=64)
    display_phone_number: str | None = Field(default=None, max_length=32)
    verified_name: str | None = Field(default=None, max_length=160)
    access_token: str | None = Field(default=None, max_length=4096)
    webhook_verify_token: str | None = Field(default=None, min_length=4, max_length=128)
    api_version: str | None = Field(default=None, max_length=16)
    is_active: bool | None = None


class WhatsappAccountResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    phone_number_id: str
    business_account_id: str | None
    display_phone_number: str | None
    verified_name: str | None
    api_version: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    # NOTE: access_token and webhook_verify_token are intentionally
    # never serialized. Use the dedicated rotate endpoints to change them.

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Webhook (audit log)
# ---------------------------------------------------------------------------


class WhatsappWebhookResponse(BaseModel):
    id: UUID
    empresa_id: UUID | None
    phone_number_id: str | None
    event_type: WhatsappWebhookEvent
    processed: bool
    error: str | None
    received_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WhatsappWebhookListResponse(BaseModel):
    items: list[WhatsappWebhookResponse]
    total: int
    limit: int
    offset: int


# ---------------------------------------------------------------------------
# Messages (inbound + outbound ledger)
# ---------------------------------------------------------------------------


class WhatsappMessageResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    account_id: UUID
    conversation_id: UUID | None
    direction: WhatsappDirection
    wa_message_id: str | None
    from_phone: str
    to_phone: str
    body: str | None
    message_type: str
    status: WhatsappMessageStatus
    error: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WhatsappMessageListResponse(BaseModel):
    items: list[WhatsappMessageResponse]
    total: int
    limit: int
    offset: int


# ---------------------------------------------------------------------------
# Send (programmatic outbound)
# ---------------------------------------------------------------------------


class WhatsappSendRequest(BaseModel):
    to_phone: str = Field(min_length=6, max_length=32)
    body: str = Field(min_length=1, max_length=4096)
    account_id: UUID | None = None
    conversation_id: UUID | None = None

    @field_validator("to_phone")
    @classmethod
    def _normalize_phone(cls, phone: str) -> str:
        cleaned = "".join(ch for ch in phone.strip() if ch.isdigit() or ch == "+")
        if cleaned.count("+") > 1 or (cleaned.startswith("+") and not cleaned[1:].isdigit()):
            raise ValueError("Invalid phone number")
        digits = cleaned.lstrip("+")
        if len(digits) < 6:
            raise ValueError("Phone number is too short")
        return digits


class WhatsappSendResponse(BaseModel):
    message: WhatsappMessageResponse
    accepted: bool
    provider_response: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Aggregate metrics
# ---------------------------------------------------------------------------


class WhatsappMetricsResponse(BaseModel):
    is_configured: bool
    active_accounts: int
    inbound_total: int
    outbound_total: int
    delivered_total: int
    failed_total: int
    pending_total: int
    inbound_last_24h: int
    outbound_last_24h: int
    webhooks_last_24h: int
    webhooks_failed_last_24h: int
    recent_webhooks: list[WhatsappWebhookResponse]
