from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.security.dependencies import TenantContext
from app.core.security.permissions import require_permission
from app.modules.conversations.dependencies import get_conversation_service
from app.modules.conversations.schemas import (
    ConversationChannel,
    ConversationCreateRequest,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationResponse,
    ConversationStatus,
    ConversationUpdateRequest,
    MessageCreateRequest,
    MessageResponse,
)
from app.modules.conversations.service import ConversationService

router = APIRouter()


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    tenant: Annotated[TenantContext, Depends(require_permission("conversations:read"))],
    service: Annotated[ConversationService, Depends(get_conversation_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
    search: Annotated[str | None, Query(min_length=1, max_length=120)] = None,
    estado: ConversationStatus | None = None,
) -> ConversationListResponse:
    return await service.list_conversations(
        tenant=tenant,
        limit=limit,
        offset=offset,
        search=search,
        estado=estado,
    )


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    payload: ConversationCreateRequest,
    tenant: Annotated[TenantContext, Depends(require_permission("conversations:write"))],
    service: Annotated[ConversationService, Depends(get_conversation_service)],
) -> ConversationResponse:
    return await service.create_conversation(tenant=tenant, payload=payload)


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: UUID,
    tenant: Annotated[TenantContext, Depends(require_permission("conversations:read"))],
    service: Annotated[ConversationService, Depends(get_conversation_service)],
) -> ConversationDetailResponse:
    return await service.get_conversation(tenant=tenant, conversation_id=conversation_id)


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    payload: ConversationUpdateRequest,
    tenant: Annotated[TenantContext, Depends(require_permission("conversations:write"))],
    service: Annotated[ConversationService, Depends(get_conversation_service)],
) -> ConversationResponse:
    return await service.update_conversation(
        tenant=tenant, conversation_id=conversation_id, payload=payload
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    tenant: Annotated[TenantContext, Depends(require_permission("conversations:write"))],
    service: Annotated[ConversationService, Depends(get_conversation_service)],
) -> None:
    await service.delete_conversation(tenant=tenant, conversation_id=conversation_id)


@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def add_message(
    conversation_id: UUID,
    payload: MessageCreateRequest,
    tenant: Annotated[TenantContext, Depends(require_permission("conversations:write"))],
    service: Annotated[ConversationService, Depends(get_conversation_service)],
) -> MessageResponse:
    return await service.add_message(tenant=tenant, conversation_id=conversation_id, payload=payload)
