"""add whatsapp business cloud api tables

Revision ID: 0012_whatsapp_business
Revises: 0011_inventory_management
Create Date: 2026-06-03
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "0012_whatsapp_business"
down_revision: str | None = "0011_inventory_management"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # whatsapp_accounts — credentials per WhatsApp phone number
    # ------------------------------------------------------------------
    op.create_table(
        "whatsapp_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "empresa_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("empresas.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("phone_number_id", sa.String(64), nullable=False),
        sa.Column("business_account_id", sa.String(64), nullable=True),
        sa.Column("display_phone_number", sa.String(32), nullable=True),
        sa.Column("verified_name", sa.String(160), nullable=True),
        sa.Column("access_token", sa.Text(), nullable=False),
        sa.Column("webhook_verify_token", sa.String(128), nullable=False),
        sa.Column("api_version", sa.String(16), nullable=False, server_default="v20.0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "empresa_id",
            "phone_number_id",
            name="uq_whatsapp_accounts__empresa_id_phone_number_id",
        ),
    )
    op.create_index(
        "idx_whatsapp_accounts__empresa_id_is_active",
        "whatsapp_accounts",
        ["empresa_id", "is_active"],
    )

    # ------------------------------------------------------------------
    # whatsapp_webhooks — immutable audit log of webhook payloads
    # ------------------------------------------------------------------
    op.create_table(
        "whatsapp_webhooks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "empresa_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("empresas.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("phone_number_id", sa.String(64), nullable=True),
        sa.Column("event_type", sa.String(32), nullable=False, server_default="unknown"),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("processed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "idx_whatsapp_webhooks__phone_number_id_created_at",
        "whatsapp_webhooks",
        ["phone_number_id", "created_at"],
    )
    op.create_index(
        "idx_whatsapp_webhooks__empresa_id_created_at",
        "whatsapp_webhooks",
        ["empresa_id", "created_at"],
    )

    # ------------------------------------------------------------------
    # whatsapp_messages — inbound + outbound ledger
    # ------------------------------------------------------------------
    op.create_table(
        "whatsapp_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "empresa_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("empresas.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("whatsapp_accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("direction", sa.String(16), nullable=False),
        sa.Column("wa_message_id", sa.String(128), nullable=True),
        sa.Column("from_phone", sa.String(32), nullable=False),
        sa.Column("to_phone", sa.String(32), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("message_type", sa.String(32), nullable=False, server_default="text"),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "direction IN ('inbound','outbound')",
            name="ck_whatsapp_messages__direction",
        ),
        sa.CheckConstraint(
            "status IN ('pending','sent','delivered','read','failed')",
            name="ck_whatsapp_messages__status",
        ),
    )
    op.create_index(
        "idx_whatsapp_messages__empresa_id_conversation_id",
        "whatsapp_messages",
        ["empresa_id", "conversation_id"],
    )
    op.create_index(
        "idx_whatsapp_messages__empresa_id_direction_created_at",
        "whatsapp_messages",
        ["empresa_id", "direction", "created_at"],
    )
    op.create_index(
        "idx_whatsapp_messages__wa_message_id",
        "whatsapp_messages",
        ["wa_message_id"],
    )
    op.create_index(
        "idx_whatsapp_messages__account_id_created_at",
        "whatsapp_messages",
        ["account_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("whatsapp_messages")
    op.drop_table("whatsapp_webhooks")
    op.drop_table("whatsapp_accounts")
