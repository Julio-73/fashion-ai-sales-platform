"""FastAPI dependencies for the WhatsApp module."""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.modules.whatsapp.cloud_api import WhatsappCloudClient
from app.modules.whatsapp.repository import (
    WhatsappAccountRepository,
    WhatsappMessageRepository,
    WhatsappWebhookRepository,
)
from app.modules.whatsapp.service import WhatsappService


# A process-wide Cloud client. It owns its own httpx.AsyncClient and
# can be safely shared across requests because we use one connection
# per call. Tests inject a mock via ``get_whatsapp_service``.
_cloud_client = WhatsappCloudClient()


def get_whatsapp_cloud_client() -> WhatsappCloudClient:
    return _cloud_client


async def get_whatsapp_account_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> WhatsappAccountRepository:
    return WhatsappAccountRepository(session=session)


async def get_whatsapp_webhook_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> WhatsappWebhookRepository:
    return WhatsappWebhookRepository(session=session)


async def get_whatsapp_message_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> WhatsappMessageRepository:
    return WhatsappMessageRepository(session=session)


async def get_whatsapp_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    account_repo: Annotated[WhatsappAccountRepository, Depends(get_whatsapp_account_repository)],
    webhook_repo: Annotated[WhatsappWebhookRepository, Depends(get_whatsapp_webhook_repository)],
    message_repo: Annotated[WhatsappMessageRepository, Depends(get_whatsapp_message_repository)],
    cloud_client: Annotated[WhatsappCloudClient, Depends(get_whatsapp_cloud_client)],
) -> WhatsappService:
    return WhatsappService(
        session=session,
        account_repo=account_repo,
        webhook_repo=webhook_repo,
        message_repo=message_repo,
        cloud_client=cloud_client,
    )
