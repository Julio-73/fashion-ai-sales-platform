from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.conversations.dependencies import get_conversation_core_service
from app.conversations.schemas import (
    ConversationCoreCreateRequest,
    ConversationCoreDetailResponse,
    ConversationCoreListResponse,
    ConversationCoreResponse,
    MessageCoreCreateRequest,
    MessageCoreListResponse,
    MessageCoreResponse,
)
from app.conversations.service import ConversationCoreService
from app.core.security.dependencies import TenantContext
from app.core.security.permissions import require_permission

router = APIRouter()


@router.post("", response_model=ConversationCoreResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    payload: ConversationCoreCreateRequest,
    tenant: Annotated[TenantContext, Depends(require_permission("conversations:write"))],
    service: Annotated[ConversationCoreService, Depends(get_conversation_core_service)],
) -> ConversationCoreResponse:
    return await service.create_conversation(tenant=tenant, payload=payload)


@router.get("", response_model=ConversationCoreListResponse)
async def list_conversations(
    tenant: Annotated[TenantContext, Depends(require_permission("conversations:read"))],
    service: Annotated[ConversationCoreService, Depends(get_conversation_core_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
    search: Annotated[str | None, Query(min_length=1, max_length=120)] = None,
    status: Annotated[str | None, Query(pattern=r"^(active|closed|converted)$")] = None,
) -> ConversationCoreListResponse:
    return await service.list_conversations(
        tenant=tenant,
        limit=limit,
        offset=offset,
        search=search,
        status=status,
    )


@router.get("/{conversation_id}", response_model=ConversationCoreDetailResponse)
async def get_conversation(
    conversation_id: UUID,
    tenant: Annotated[TenantContext, Depends(require_permission("conversations:read"))],
    service: Annotated[ConversationCoreService, Depends(get_conversation_core_service)],
) -> ConversationCoreDetailResponse:
    return await service.get_conversation(tenant=tenant, conversation_id=conversation_id)


@router.post("/{conversation_id}/messages", response_model=MessageCoreResponse, status_code=status.HTTP_201_CREATED)
async def add_message(
    conversation_id: UUID,
    payload: MessageCoreCreateRequest,
    tenant: Annotated[TenantContext, Depends(require_permission("conversations:write"))],
    service: Annotated[ConversationCoreService, Depends(get_conversation_core_service)],
) -> MessageCoreResponse:
    return await service.add_message(tenant=tenant, conversation_id=conversation_id, payload=payload)


@router.get("/{conversation_id}/messages", response_model=MessageCoreListResponse)
async def list_messages(
    conversation_id: UUID,
    tenant: Annotated[TenantContext, Depends(require_permission("conversations:read"))],
    service: Annotated[ConversationCoreService, Depends(get_conversation_core_service)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> MessageCoreListResponse:
    return await service.list_messages(
        tenant=tenant,
        conversation_id=conversation_id,
        limit=limit,
        offset=offset,
    )
