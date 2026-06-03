"""Business logic for the WhatsApp Business Cloud API integration.

This module deliberately orchestrates existing services from
``conversations``, ``customers`` and ``smart_sales`` without
modifying any of them:

* ``AutoReplyGenerator.process_message`` is used to let the Smart Sales
  Brain (which is FROZEN) craft a response.
* ``CustomerService.create_customer`` is used to auto-provision a
  ``Cliente`` the first time a phone number writes to us.
* ``ConversationRepository`` is used to find / create the per-phone
  conversation.

We never reach into the internals of those modules.

NOTE: ``ConversationRepository`` is a FROZEN module, so we don't add a
custom ``find_open_for_customer`` helper there. We perform a
read-only direct query against the same ``Conversation`` model from
this module instead. No schema changes, no behaviour changes to the
frozen module.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.security.dependencies import TenantContext
from app.modules.conversations.ai_reply import AutoReplyGenerator
from app.modules.conversations.models import Conversation as ConversationModel
from app.modules.conversations.repository import ConversationRepository
from app.modules.conversations.schemas import (
    ConversationCreateRequest,
    ProcessMessageRequest,
)
from app.modules.customers.repository import CustomerRepository
from app.modules.customers.schemas import CustomerCreateRequest
from app.modules.customers.service import CustomerService
from app.modules.whatsapp.cloud_api import (
    WhatsappCloudClient,
    normalize_phone_for_storage,
)
from app.modules.whatsapp.models import (
    WHATSAPP_DIRECTIONS,
    WHATSAPP_MESSAGE_STATUSES,
    WHATSAPP_WEBHOOK_EVENTS,
)
from app.modules.whatsapp.repository import (
    WhatsappAccountRepository,
    WhatsappMessageRepository,
    WhatsappWebhookRepository,
)
from app.modules.whatsapp.schemas import (
    WhatsappAccountCreateRequest,
    WhatsappAccountResponse,
    WhatsappAccountUpdateRequest,
    WhatsappMessageResponse,
    WhatsappMetricsResponse,
    WhatsappSendRequest,
    WhatsappSendResponse,
    WhatsappWebhookResponse,
)

logger = logging.getLogger("ai_sales_agent.whatsapp.service")

# Permissions the integration needs to perform write operations on
# conversations and customers. These are pre-baked into the synthetic
# tenant we build for webhook-driven flows.
_WHATSAPP_PERMISSIONS: set[str] = {
    "customers:read",
    "customers:write",
    "conversations:read",
    "conversations:write",
    "products:read",
    "orders:read",
    "orders:write",
}


# ---------------------------------------------------------------------------
# Synthetic tenant used by the webhook (no JWT is available)
# ---------------------------------------------------------------------------


def _synthetic_tenant(empresa_id: UUID) -> TenantContext:
    return TenantContext(
        empresa_id=empresa_id,
        user_id=UUID("00000000-0000-0000-0000-000000000000"),
        roles=["whatsapp_integration"],
        permissions=set(_WHATSAPP_PERMISSIONS),
    )


# ---------------------------------------------------------------------------
# Account CRUD
# ---------------------------------------------------------------------------


class WhatsappService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        account_repo: WhatsappAccountRepository,
        webhook_repo: WhatsappWebhookRepository,
        message_repo: WhatsappMessageRepository,
        cloud_client: WhatsappCloudClient | None = None,
    ) -> None:
        self._session = session
        self._account_repo = account_repo
        self._webhook_repo = webhook_repo
        self._message_repo = message_repo
        self._cloud = cloud_client or WhatsappCloudClient()

    # -----------------------------------------------------------------
    # Accounts
    # -----------------------------------------------------------------

    async def create_account(
        self,
        *,
        tenant: TenantContext,
        payload: WhatsappAccountCreateRequest,
    ) -> WhatsappAccountResponse:
        try:
            account = await self._account_repo.create(
                empresa_id=tenant.empresa_id,
                phone_number_id=payload.phone_number_id,
                business_account_id=payload.business_account_id,
                display_phone_number=payload.display_phone_number,
                verified_name=payload.verified_name,
                access_token=payload.access_token,
                webhook_verify_token=payload.webhook_verify_token,
                api_version=payload.api_version,
                is_active=payload.is_active,
            )
            await self._account_repo.commit()
        except Exception as exc:  # noqa: BLE001
            await self._account_repo.rollback()
            raise AppError(
                code="whatsapp_account_conflict",
                message="Failed to create WhatsApp account",
                status_code=409,
            ) from exc
        return WhatsappAccountResponse.model_validate(account)

    async def update_account(
        self,
        *,
        tenant: TenantContext,
        account_id: UUID,
        payload: WhatsappAccountUpdateRequest,
    ) -> WhatsappAccountResponse:
        account = await self._account_repo.get_by_id(
            empresa_id=tenant.empresa_id, account_id=account_id
        )
        if account is None:
            raise AppError(
                code="whatsapp_account_not_found",
                message="WhatsApp account not found",
                status_code=404,
            )
        updates = payload.model_dump(exclude_unset=True)
        updated = await self._account_repo.update(account=account, payload=updates)
        await self._account_repo.commit()
        return WhatsappAccountResponse.model_validate(updated)

    async def list_accounts(
        self, *, tenant: TenantContext
    ) -> list[WhatsappAccountResponse]:
        accounts = await self._account_repo.list_all(empresa_id=tenant.empresa_id)
        return [WhatsappAccountResponse.model_validate(a) for a in accounts]

    async def get_account(
        self, *, tenant: TenantContext, account_id: UUID
    ) -> WhatsappAccountResponse:
        account = await self._account_repo.get_by_id(
            empresa_id=tenant.empresa_id, account_id=account_id
        )
        if account is None:
            raise AppError(
                code="whatsapp_account_not_found",
                message="WhatsApp account not found",
                status_code=404,
            )
        return WhatsappAccountResponse.model_validate(account)

    async def delete_account(
        self, *, tenant: TenantContext, account_id: UUID
    ) -> None:
        account = await self._account_repo.get_by_id(
            empresa_id=tenant.empresa_id, account_id=account_id
        )
        if account is None:
            raise AppError(
                code="whatsapp_account_not_found",
                message="WhatsApp account not found",
                status_code=404,
            )
        await self._account_repo.soft_delete(account=account)
        await self._account_repo.commit()

    # -----------------------------------------------------------------
    # Outbound messages
    # -----------------------------------------------------------------

    async def send_message(
        self,
        *,
        tenant: TenantContext,
        payload: WhatsappSendRequest,
    ) -> WhatsappSendResponse:
        """Send a message and persist a ledger row.

        The conversation is optional. If omitted, a stub conversation
        will not be created — the outbound message simply has
        ``conversation_id=None``. Recipients can also be reached when
        the operator just wants to push a transactional message.
        """
        account = await self._resolve_account(
            tenant=tenant, account_id=payload.account_id
        )
        to_phone = payload.to_phone
        try:
            provider_response = await self._cloud.send_text_message(
                phone_number_id=account.phone_number_id,
                access_token=account.access_token,
                to_phone=to_phone,
                body=payload.body,
            )
            wa_message_id = (
                provider_response.get("messages", [{}])[0].get("id")
                if isinstance(provider_response.get("messages"), list)
                else provider_response.get("synthetic_id")
            )
            status_value = "sent" if not provider_response.get("dry_run") else "sent"
            error_value: str | None = None
            accepted = True
        except Exception as exc:  # noqa: BLE001
            logger.warning("WhatsApp send failed: %s", exc)
            provider_response = {"error": str(exc)}
            wa_message_id = None
            status_value = "failed"
            error_value = str(exc)
            accepted = False

        stored = await self._message_repo.create(
            empresa_id=tenant.empresa_id,
            account_id=account.id,
            conversation_id=payload.conversation_id,
            direction="outbound",
            wa_message_id=wa_message_id,
            from_phone=account.display_phone_number or account.phone_number_id,
            to_phone=to_phone,
            body=payload.body,
            message_type="text",
            status=status_value,
            error=error_value,
            raw_payload=provider_response if isinstance(provider_response, dict) else None,
        )
        await self._message_repo.commit()

        return WhatsappSendResponse(
            message=WhatsappMessageResponse.model_validate(stored),
            accepted=accepted,
            provider_response=provider_response if isinstance(provider_response, dict) else None,
        )

    # -----------------------------------------------------------------
    # Inbound messages (webhook handler)
    # -----------------------------------------------------------------

    async def process_inbound_webhook(
        self,
        *,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Handle a raw Meta Cloud API webhook payload.

        Returns a small summary (counts of received / processed /
        failed messages) so the HTTP layer can serialise it.
        """
        inbound = WhatsappCloudClient.extract_inbound_messages(payload)
        if not inbound:
            # Could be a status update or an unknown payload — log and exit.
            phone_id = _first_phone_number_id(payload)
            webhook = await self._webhook_repo.record(
                empresa_id=None,
                phone_number_id=phone_id,
                event_type=_classify_event(payload),
                payload=payload,
            )
            await self._webhook_repo.mark_processed(webhook=webhook, error=None)
            await self._webhook_repo.commit()
            return {"received": 0, "processed": 0, "failed": 0}

        processed = 0
        failed = 0
        for item in inbound:
            try:
                await self._handle_single_inbound(
                    phone_number_id=item.get("phone_number_id"),
                    message=item.get("message") or {},
                    contacts=item.get("contacts") or [],
                    raw_payload=payload,
                )
                processed += 1
            except Exception:  # noqa: BLE001
                logger.exception("Failed to process inbound WhatsApp message")
                failed += 1

        return {"received": len(inbound), "processed": processed, "failed": failed}

    async def _handle_single_inbound(
        self,
        *,
        phone_number_id: str | None,
        message: dict[str, Any],
        contacts: list[dict[str, Any]],
        raw_payload: dict[str, Any],
    ) -> None:
        if not phone_number_id:
            raise AppError(
                code="whatsapp_webhook_invalid",
                message="Missing phone_number_id in webhook payload",
                status_code=400,
            )
        account = await self._account_repo.get_by_phone_number_id(
            phone_number_id=phone_number_id
        )
        if account is None or not account.is_active:
            webhook = await self._webhook_repo.record(
                empresa_id=account.empresa_id if account else None,
                phone_number_id=phone_number_id,
                event_type="message",
                payload=raw_payload,
            )
            await self._webhook_repo.mark_processed(
                webhook=webhook,
                error="No active WhatsApp account for this phone_number_id",
            )
            await self._webhook_repo.commit()
            raise AppError(
                code="whatsapp_account_not_found",
                message="No active WhatsApp account for this phone_number_id",
                status_code=404,
            )

        webhook = await self._webhook_repo.record(
            empresa_id=account.empresa_id,
            phone_number_id=phone_number_id,
            event_type="message",
            payload=raw_payload,
        )

        try:
            text = _extract_text(message)
            if not text:
                await self._webhook_repo.mark_processed(
                    webhook=webhook, error="Unsupported message type (no text body)"
                )
                await self._webhook_repo.commit()
                return

            from_phone = normalize_phone_for_storage(message.get("from") or "")
            wa_message_id = message.get("id")
            display_name = _extract_display_name(contacts, message.get("from"))

            # 1) Resolve or create the customer.
            customer = await self._find_or_create_customer(
                empresa_id=account.empresa_id,
                phone=from_phone,
                display_name=display_name,
            )

            # 2) Resolve or create the conversation.
            conversation = await self._find_or_create_conversation(
                empresa_id=account.empresa_id,
                cliente_id=customer.id,
                preview=text,
            )

            # 3) Persist the inbound row.
            inbound_row = await self._message_repo.create(
                empresa_id=account.empresa_id,
                account_id=account.id,
                conversation_id=conversation.id,
                direction="inbound",
                wa_message_id=wa_message_id,
                from_phone=from_phone,
                to_phone=account.display_phone_number or account.phone_number_id,
                body=text,
                message_type=message.get("type") or "text",
                status="delivered",
                error=None,
                raw_payload=message,
            )
            await self._message_repo.commit()

            # 4) Invoke the Smart Sales brain via the conversations
            #    module. process_message stores the inbound message +
            #    the AI reply and commits them.
            conversation_repo = ConversationRepository(session=self._session)
            auto_reply = AutoReplyGenerator(
                session=self._session,
                repository=conversation_repo,
            )
            process_payload = ProcessMessageRequest(
                role="client",
                content=text,
                sender_name=display_name or "Cliente WhatsApp",
            )
            try:
                result = await auto_reply.process_message(
                    empresa_id=account.empresa_id,
                    conversation_id=conversation.id,
                    payload=process_payload,
                )
            except Exception:  # noqa: BLE001
                logger.exception(
                    "AutoReply failed for conversation %s; skipping outbound",
                    conversation.id,
                )
                await self._webhook_repo.mark_processed(webhook=webhook, error=None)
                await self._webhook_repo.commit()
                return

            ai_text = result.ai_reply.content if result.ai_reply else None
            await self._webhook_repo.mark_processed(webhook=webhook, error=None)
            await self._webhook_repo.commit()

            # 5) Send the AI reply via the Cloud API and log the result.
            if ai_text:
                await self._send_and_record_outbound(
                    account=account,
                    conversation_id=conversation.id,
                    inbound_row_id=inbound_row.id,
                    to_phone=from_phone,
                    body=ai_text,
                )
        except Exception as exc:  # noqa: BLE001
            await self._webhook_repo.mark_processed(
                webhook=webhook, error=str(exc)
            )
            await self._webhook_repo.commit()
            raise

    async def _send_and_record_outbound(
        self,
        *,
        account,
        conversation_id: UUID,
        inbound_row_id: UUID,
        to_phone: str,
        body: str,
    ) -> None:
        try:
            provider_response = await self._cloud.send_text_message(
                phone_number_id=account.phone_number_id,
                access_token=account.access_token,
                to_phone=to_phone,
                body=body,
            )
            wa_message_id = (
                provider_response.get("messages", [{}])[0].get("id")
                if isinstance(provider_response.get("messages"), list)
                else provider_response.get("synthetic_id")
            )
            status_value = "sent"
            error_value: str | None = None
        except Exception as exc:  # noqa: BLE001
            logger.warning("Cloud API outbound failed: %s", exc)
            provider_response = {"error": str(exc)}
            wa_message_id = None
            status_value = "failed"
            error_value = str(exc)

        await self._message_repo.create(
            empresa_id=account.empresa_id,
            account_id=account.id,
            conversation_id=conversation_id,
            direction="outbound",
            wa_message_id=wa_message_id,
            from_phone=account.display_phone_number or account.phone_number_id,
            to_phone=to_phone,
            body=body,
            message_type="text",
            status=status_value,
            error=error_value,
            raw_payload=provider_response if isinstance(provider_response, dict) else None,
        )
        await self._message_repo.commit()
        _ = inbound_row_id  # reserved for future use (linked delivery receipts)

    # -----------------------------------------------------------------
    # Metrics
    # -----------------------------------------------------------------

    async def get_metrics(
        self, *, tenant: TenantContext
    ) -> WhatsappMetricsResponse:
        accounts = await self._account_repo.list_all(empresa_id=tenant.empresa_id)
        active = [a for a in accounts if a.is_active]
        since = datetime.now(UTC) - timedelta(hours=24)
        message_counts = await self._message_repo.counts_since(
            empresa_id=tenant.empresa_id, since=since
        )
        webhooks_24h = await self._webhook_repo.count_since(
            empresa_id=tenant.empresa_id, since=since
        )
        webhooks_failed_24h = await self._webhook_repo.count_since(
            empresa_id=tenant.empresa_id, since=since, only_failed=True
        )
        recent_webhooks, _ = await self._webhook_repo.list_recent(
            empresa_id=tenant.empresa_id, limit=5, offset=0
        )
        return WhatsappMetricsResponse(
            is_configured=len(active) > 0,
            active_accounts=len(active),
            inbound_total=message_counts["inbound"],
            outbound_total=message_counts["outbound"],
            delivered_total=message_counts["delivered"],
            failed_total=message_counts["failed"],
            pending_total=message_counts["pending"],
            inbound_last_24h=message_counts["inbound"],
            outbound_last_24h=message_counts["outbound"],
            webhooks_last_24h=webhooks_24h,
            webhooks_failed_last_24h=webhooks_failed_24h,
            recent_webhooks=[
                WhatsappWebhookResponse.model_validate(w) for w in recent_webhooks
            ],
        )

    async def list_webhooks(
        self, *, tenant: TenantContext, limit: int, offset: int
    ) -> tuple[list[WhatsappWebhookResponse], int]:
        webhooks, total = await self._webhook_repo.list_recent(
            empresa_id=tenant.empresa_id, limit=limit, offset=offset
        )
        return [WhatsappWebhookResponse.model_validate(w) for w in webhooks], total

    async def list_messages(
        self,
        *,
        tenant: TenantContext,
        limit: int,
        offset: int,
        direction: str | None = None,
    ) -> tuple[list[WhatsappMessageResponse], int]:
        if direction and direction not in WHATSAPP_DIRECTIONS:
            raise AppError(
                code="whatsapp_invalid_direction",
                message="Invalid direction",
                status_code=422,
            )
        rows, total = await self._message_repo.list(
            empresa_id=tenant.empresa_id,
            limit=limit,
            offset=offset,
            direction=direction,
        )
        return [WhatsappMessageResponse.model_validate(r) for r in rows], total

    # -----------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------

    async def _resolve_account(
        self, *, tenant: TenantContext, account_id: UUID | None
    ):
        if account_id:
            account = await self._account_repo.get_by_id(
                empresa_id=tenant.empresa_id, account_id=account_id
            )
            if account is None or not account.is_active:
                raise AppError(
                    code="whatsapp_account_not_found",
                    message="WhatsApp account not found",
                    status_code=404,
                )
            return account
        actives = await self._account_repo.list_active(empresa_id=tenant.empresa_id)
        if not actives:
            raise AppError(
                code="whatsapp_account_not_configured",
                message="No active WhatsApp accounts configured",
                status_code=409,
            )
        return actives[0]

    async def _find_or_create_customer(
        self,
        *,
        empresa_id: UUID,
        phone: str,
        display_name: str | None,
    ):
        customer_repo = CustomerRepository(session=self._session)
        existing = await customer_repo.find_by_phone(
            empresa_id=empresa_id, phone=phone
        )
        if existing is not None:
            return existing
        full_name = (display_name or f"Cliente WhatsApp {phone[-4:]}").strip()[:160]
        create_payload = CustomerCreateRequest(
            full_name=full_name,
            phone=phone,
            whatsapp=phone,
            tags=["whatsapp"],
            source="whatsapp",
            lead_status="new",
        )
        # Use the public CustomerService so any side-effects (DOs, sanitize,
        # future hooks) are honoured. We bypass router-level permission
        # checks by constructing a synthetic tenant with all relevant
        # permissions.
        tenant = _synthetic_tenant(empresa_id)
        service = CustomerService(repository=customer_repo)
        try:
            customer = await service.create_customer(tenant=tenant, payload=create_payload)
        except AppError as exc:
            # Race: another webhook created the customer concurrently. Retry
            # the lookup once.
            if exc.code == "customer_conflict":
                refound = await customer_repo.find_by_phone(
                    empresa_id=empresa_id, phone=phone
                )
                if refound is not None:
                    return refound
            raise
        # Reload the row to get a managed instance.
        return await customer_repo.get_by_id(
            empresa_id=empresa_id, customer_id=customer.id
        )

    async def _find_or_create_conversation(
        self,
        *,
        empresa_id: UUID,
        cliente_id: UUID,
        preview: str,
    ):
        existing = await self._find_open_conversation(
            empresa_id=empresa_id,
            cliente_id=cliente_id,
        )
        if existing is not None:
            return existing
        conversation_repo = ConversationRepository(session=self._session)
        try:
            created = await conversation_repo.create_conversation(
                empresa_id=empresa_id,
                payload=ConversationCreateRequest(
                    cliente_id=cliente_id,
                    asunto=preview[:80],
                    canal="whatsapp",
                ),
            )
            await conversation_repo.commit()
            return created
        except Exception:  # noqa: BLE001
            await conversation_repo.rollback()
            refound = await self._find_open_conversation(
                empresa_id=empresa_id,
                cliente_id=cliente_id,
            )
            if refound is not None:
                return refound
            raise

    async def _find_open_conversation(
        self,
        *,
        empresa_id: UUID,
        cliente_id: UUID,
    ):
        # Read-only direct query against the FROZEN conversations
        # module's SQLAlchemy model. We never mutate it; we only read.
        result = await self._session.execute(
            select(ConversationModel)
            .where(
                ConversationModel.empresa_id == empresa_id,
                ConversationModel.cliente_id == cliente_id,
                ConversationModel.canal == "whatsapp",
                ConversationModel.deleted_at.is_(None),
                ConversationModel.estado.in_(("open", "pending")),
            )
            .order_by(ConversationModel.updated_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Pure helpers (parsing)
# ---------------------------------------------------------------------------


def _extract_text(message: dict[str, Any]) -> str | None:
    msg_type = message.get("type")
    if msg_type == "text":
        body = (message.get("text") or {}).get("body")
        if body:
            return str(body).strip()
    return None


def _extract_display_name(contacts: list[dict[str, Any]], phone: str | None) -> str | None:
    for contact in contacts:
        if not isinstance(contact, dict):
            continue
        if phone and contact.get("wa_id") and contact.get("wa_id") != phone:
            continue
        profile = contact.get("profile") or {}
        name = profile.get("name")
        if name:
            return str(name).strip()[:160]
    return None


def _classify_event(payload: dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        return "unknown"
    if "entry" not in payload:
        return "unknown"
    for entry in payload.get("entry") or []:
        if not isinstance(entry, dict):
            continue
        for change in entry.get("changes") or []:
            value = (change or {}).get("value") or {}
            if value.get("messages"):
                return "message"
            if value.get("statuses"):
                return "status"
    return "unknown"


def _first_phone_number_id(payload: dict[str, Any]) -> str | None:
    if not isinstance(payload, dict):
        return None
    for entry in payload.get("entry") or []:
        if not isinstance(entry, dict):
            continue
        for change in entry.get("changes") or []:
            metadata = ((change or {}).get("value") or {}).get("metadata") or {}
            phone_id = metadata.get("phone_number_id")
            if phone_id:
                return str(phone_id)
    return None


# Re-export for tests that import the package surface.
__all__ = [
    "WhatsappService",
    "WHATSAPP_DIRECTIONS",
    "WHATSAPP_MESSAGE_STATUSES",
    "WHATSAPP_WEBHOOK_EVENTS",
]
