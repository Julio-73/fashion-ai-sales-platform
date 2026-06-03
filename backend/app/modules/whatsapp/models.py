"""SQLAlchemy models for the WhatsApp Business Cloud API integration.

These tables are scoped to ``empresa_id`` and never imported by the
frozen modules (conversations, smart_sales, crm, orders, inventory).
The integration reaches them only through their public services and
repository classes.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TenantMixin, TimestampMixin, UUIDPrimaryKeyMixin


# Direction of a stored whatsapp_message row.
WHATSAPP_DIRECTIONS = ("inbound", "outbound")

# Lifecycle status of an outbound message.
WHATSAPP_MESSAGE_STATUSES = (
    "pending",   # queued in our DB, not yet sent to Cloud API
    "sent",      # Cloud API accepted it
    "delivered", # Meta confirmed delivery to the user's device
    "read",      # Meta confirmed read receipt
    "failed",    # Cloud API returned an error
)

# Event types we record from webhooks.
WHATSAPP_WEBHOOK_EVENTS = (
    "verification",  # GET handshake (challenge)
    "message",       # inbound text/media
    "status",        # delivery receipts
    "unknown",
)


class WhatsappAccount(UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin, Base):
    """Credentials for a WhatsApp Business phone number, scoped per tenant.

    Each row stores the Meta Cloud API ``phone_number_id`` plus the
    access token and webhook verify token. Tokens are persisted as-is
    (we expect the deployment to keep the database encrypted at rest).
    """

    __tablename__ = "whatsapp_accounts"
    __table_args__ = (
        UniqueConstraint(
            "empresa_id",
            "phone_number_id",
            name="uq_whatsapp_accounts__empresa_id_phone_number_id",
        ),
        Index(
            "idx_whatsapp_accounts__empresa_id_is_active",
            "empresa_id",
            "is_active",
        ),
    )

    phone_number_id: Mapped[str] = mapped_column(String(64), nullable=False)
    business_account_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    display_phone_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    verified_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    webhook_verify_token: Mapped[str] = mapped_column(String(128), nullable=False)
    api_version: Mapped[str] = mapped_column(String(16), nullable=False, default="v20.0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")


class WhatsappWebhook(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Immutable audit log of every webhook payload Meta sends us.

    ``empresa_id`` is nullable: during the GET verification handshake we
    don't know the tenant yet, so we log the payload under NULL and
    resolve it later when the corresponding ``phone_number_id`` is
    registered.
    """

    __tablename__ = "whatsapp_webhooks"
    __table_args__ = (
        Index("idx_whatsapp_webhooks__phone_number_id_created_at", "phone_number_id", "created_at"),
        Index("idx_whatsapp_webhooks__empresa_id_created_at", "empresa_id", "created_at"),
    )

    empresa_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    phone_number_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    processed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class WhatsappMessage(UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin, Base):
    """Per-message ledger (inbound + outbound) with Meta correlation IDs.

    We never mutate a row's ``direction``: it's set at insert time.
    ``status`` only applies to outbound rows.
    """

    __tablename__ = "whatsapp_messages"
    __table_args__ = (
        CheckConstraint(
            "direction IN ('inbound','outbound')",
            name="ck_whatsapp_messages__direction",
        ),
        CheckConstraint(
            "status IN ('pending','sent','delivered','read','failed')",
            name="ck_whatsapp_messages__status",
        ),
        Index("idx_whatsapp_messages__empresa_id_conversation_id", "empresa_id", "conversation_id"),
        Index("idx_whatsapp_messages__empresa_id_direction_created_at", "empresa_id", "direction", "created_at"),
        Index("idx_whatsapp_messages__wa_message_id", "wa_message_id"),
        Index("idx_whatsapp_messages__account_id_created_at", "account_id", "created_at"),
    )

    account_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("whatsapp_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    conversation_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
    )
    direction: Mapped[str] = mapped_column(String(16), nullable=False)
    wa_message_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    from_phone: Mapped[str] = mapped_column(String(32), nullable=False)
    to_phone: Mapped[str] = mapped_column(String(32), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    message_type: Mapped[str] = mapped_column(String(32), nullable=False, default="text")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
