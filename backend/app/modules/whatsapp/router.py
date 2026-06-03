"""REST + webhook router for the WhatsApp Business Cloud API integration.

The webhook endpoints are intentionally unauthenticated — Meta posts
them without a JWT. Tenant isolation is enforced by looking up the
sender ``phone_number_id`` in the ``whatsapp_accounts`` table.
"""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status
from pydantic import BaseModel, Field

from app.core.security.dependencies import TenantContext
from app.core.security.permissions import require_permission
from app.modules.whatsapp.dependencies import get_whatsapp_service
from app.modules.whatsapp.schemas import (
    WhatsappAccountCreateRequest,
    WhatsappAccountResponse,
    WhatsappAccountUpdateRequest,
    WhatsappMessageListResponse,
    WhatsappMetricsResponse,
    WhatsappSendRequest,
    WhatsappSendResponse,
    WhatsappWebhookListResponse,
)
from app.modules.whatsapp.service import WhatsappService


router = APIRouter()


# ---------------------------------------------------------------------------
# Webhook (public, called by Meta)
# ---------------------------------------------------------------------------


class WebhookChallengeResponse(BaseModel):
    challenge: str = Field(..., description="Echoed back to Meta for verification")


@router.get("/webhook", response_model=WebhookChallengeResponse)
async def verify_webhook(
    request: Request,
    service: Annotated[WhatsappService, Depends(get_whatsapp_service)],
) -> WebhookChallengeResponse:
    """Meta's webhook verification handshake.

    Meta sends a GET with ``hub.mode=subscribe``, ``hub.verify_token`` and
    ``hub.challenge``. We must echo the challenge back to confirm the
    endpoint. The ``verify_token`` we accept is the one configured in
    *any* active ``whatsapp_accounts`` row (per Meta the same token is
    used for the whole webhook subscription).
    """
    params = dict(request.query_params)
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    if mode != "subscribe" or not challenge:
        from app.core.errors import AppError

        raise AppError(
            code="whatsapp_webhook_invalid",
            message="Invalid webhook verification request",
            status_code=400,
        )
    # The verify token is global per webhook subscription. We accept the
    # challenge as long as *some* active account declares it.
    from sqlalchemy import select

    from app.modules.whatsapp.models import WhatsappAccount

    session = service._session  # type: ignore[attr-defined]
    result = await session.execute(
        select(WhatsappAccount).where(WhatsappAccount.is_active.is_(True))
    )
    accounts = result.scalars().all()
    if not any(a.webhook_verify_token == token for a in accounts):
        from app.core.errors import AppError

        raise AppError(
            code="whatsapp_webhook_invalid",
            message="Verify token does not match",
            status_code=403,
        )
    return WebhookChallengeResponse(challenge=challenge)


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def receive_webhook(
    request: Request,
    service: Annotated[WhatsappService, Depends(get_whatsapp_service)],
) -> dict[str, int]:
    """Receive a Meta Cloud API webhook payload.

    The endpoint always returns 200 once we've persisted the payload;
    errors are stored in ``whatsapp_webhooks.error`` so the operator can
    inspect them in the dashboard.
    """
    try:
        payload = await request.json()
    except Exception:  # noqa: BLE001
        from app.core.errors import AppError

        raise AppError(
            code="whatsapp_webhook_invalid",
            message="Invalid JSON payload",
            status_code=400,
        ) from None
    if not isinstance(payload, dict):
        from app.core.errors import AppError

        raise AppError(
            code="whatsapp_webhook_invalid",
            message="Webhook payload must be a JSON object",
            status_code=400,
        )
    summary = await service.process_inbound_webhook(payload=payload)
    return summary


# ---------------------------------------------------------------------------
# Authenticated management endpoints
# ---------------------------------------------------------------------------


@router.get("/metrics", response_model=WhatsappMetricsResponse)
async def get_metrics(
    tenant: Annotated[TenantContext, Depends(require_permission("whatsapp:read"))],
    service: Annotated[WhatsappService, Depends(get_whatsapp_service)],
) -> WhatsappMetricsResponse:
    return await service.get_metrics(tenant=tenant)


@router.get("/accounts", response_model=list[WhatsappAccountResponse])
async def list_accounts(
    tenant: Annotated[TenantContext, Depends(require_permission("whatsapp:read"))],
    service: Annotated[WhatsappService, Depends(get_whatsapp_service)],
) -> list[WhatsappAccountResponse]:
    return await service.list_accounts(tenant=tenant)


@router.post(
    "/accounts",
    response_model=WhatsappAccountResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_account(
    payload: WhatsappAccountCreateRequest,
    tenant: Annotated[TenantContext, Depends(require_permission("whatsapp:admin"))],
    service: Annotated[WhatsappService, Depends(get_whatsapp_service)],
) -> WhatsappAccountResponse:
    return await service.create_account(tenant=tenant, payload=payload)


@router.get("/accounts/{account_id}", response_model=WhatsappAccountResponse)
async def get_account(
    account_id: UUID,
    tenant: Annotated[TenantContext, Depends(require_permission("whatsapp:read"))],
    service: Annotated[WhatsappService, Depends(get_whatsapp_service)],
) -> WhatsappAccountResponse:
    return await service.get_account(tenant=tenant, account_id=account_id)


@router.patch("/accounts/{account_id}", response_model=WhatsappAccountResponse)
async def update_account(
    account_id: UUID,
    payload: WhatsappAccountUpdateRequest,
    tenant: Annotated[TenantContext, Depends(require_permission("whatsapp:admin"))],
    service: Annotated[WhatsappService, Depends(get_whatsapp_service)],
) -> WhatsappAccountResponse:
    return await service.update_account(
        tenant=tenant, account_id=account_id, payload=payload
    )


@router.delete(
    "/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_account(
    account_id: UUID,
    tenant: Annotated[TenantContext, Depends(require_permission("whatsapp:admin"))],
    service: Annotated[WhatsappService, Depends(get_whatsapp_service)],
) -> Response:
    await service.delete_account(tenant=tenant, account_id=account_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/send", response_model=WhatsappSendResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    payload: WhatsappSendRequest,
    tenant: Annotated[TenantContext, Depends(require_permission("whatsapp:write"))],
    service: Annotated[WhatsappService, Depends(get_whatsapp_service)],
) -> WhatsappSendResponse:
    return await service.send_message(tenant=tenant, payload=payload)


@router.get("/webhooks", response_model=WhatsappWebhookListResponse)
async def list_webhooks(
    tenant: Annotated[TenantContext, Depends(require_permission("whatsapp:read"))],
    service: Annotated[WhatsappService, Depends(get_whatsapp_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> WhatsappWebhookListResponse:
    items, total = await service.list_webhooks(
        tenant=tenant, limit=limit, offset=offset
    )
    return WhatsappWebhookListResponse(
        items=items, total=total, limit=limit, offset=offset
    )


@router.get("/messages", response_model=WhatsappMessageListResponse)
async def list_messages(
    tenant: Annotated[TenantContext, Depends(require_permission("whatsapp:read"))],
    service: Annotated[WhatsappService, Depends(get_whatsapp_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
    direction: Annotated[str | None, Query(pattern="^(inbound|outbound)$")] = None,
) -> WhatsappMessageListResponse:
    items, total = await service.list_messages(
        tenant=tenant, limit=limit, offset=offset, direction=direction
    )
    return WhatsappMessageListResponse(
        items=items, total=total, limit=limit, offset=offset
    )
