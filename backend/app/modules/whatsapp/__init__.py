"""WhatsApp Business Cloud API integration (Enterprise V1).

This package adds a thin integration layer on top of the existing
``conversations``, ``customers`` and ``smart_sales`` modules without
modifying any of them. See ``service.py`` for the orchestration logic.
"""
from app.modules.whatsapp.models import (
    WhatsappAccount,
    WhatsappMessage,
    WhatsappWebhook,
)
from app.modules.whatsapp.schemas import (
    WhatsappAccountCreateRequest,
    WhatsappAccountResponse,
    WhatsappAccountUpdateRequest,
    WhatsappMessageListResponse,
    WhatsappMessageResponse,
    WhatsappMetricsResponse,
    WhatsappSendRequest,
    WhatsappSendResponse,
    WhatsappWebhookListResponse,
    WhatsappWebhookResponse,
)
from app.modules.whatsapp.service import WhatsappService

__all__ = [
    "WhatsappAccount",
    "WhatsappWebhook",
    "WhatsappMessage",
    "WhatsappService",
    "WhatsappAccountCreateRequest",
    "WhatsappAccountResponse",
    "WhatsappAccountUpdateRequest",
    "WhatsappMessageListResponse",
    "WhatsappMessageResponse",
    "WhatsappMetricsResponse",
    "WhatsappSendRequest",
    "WhatsappSendResponse",
    "WhatsappWebhookListResponse",
    "WhatsappWebhookResponse",
]
