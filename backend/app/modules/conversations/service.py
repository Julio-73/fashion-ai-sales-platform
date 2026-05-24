from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.core.errors import AppError
from app.core.security.dependencies import TenantContext
from app.modules.conversations.dtos import ConversationDTO, MessageDTO
from app.modules.conversations.repository import ConversationRepository
from app.modules.conversations.schemas import (
    ConversationCreateRequest,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationResponse,
    ConversationUpdateRequest,
    MessageCreateRequest,
    MessageResponse,
)


class ConversationService:
    def __init__(self, repository: ConversationRepository) -> None:
        self._repository = repository

    async def create_conversation(
        self,
        *,
        tenant: TenantContext,
        payload: ConversationCreateRequest,
    ) -> ConversationResponse:
        try:
            conversation = await self._repository.create_conversation(
                empresa_id=tenant.empresa_id, payload=payload
            )
            await self._repository.commit()
            return ConversationResponse.model_validate(ConversationDTO.model_validate(conversation))
        except IntegrityError as exc:
            await self._repository.rollback()
            raise AppError(code="conversation_conflict", message="Failed to create conversation", status_code=409) from exc

    async def get_conversation(
        self,
        *,
        tenant: TenantContext,
        conversation_id: UUID,
    ) -> ConversationDetailResponse:
        conversation = await self._get_conversation_or_404(
            empresa_id=tenant.empresa_id, conversation_id=conversation_id
        )
        messages, _ = await self._repository.list_messages(
            empresa_id=tenant.empresa_id,
            conversation_id=conversation_id,
            limit=200,
            offset=0,
        )
        return ConversationDetailResponse(
            **ConversationDTO.model_validate(conversation).model_dump(),
            messages=[MessageResponse.model_validate(MessageDTO.model_validate(m)) for m in messages],
        )

    async def list_conversations(
        self,
        *,
        tenant: TenantContext,
        limit: int,
        offset: int,
        search: str | None,
        estado: str | None,
    ) -> ConversationListResponse:
        conversations, total = await self._repository.list_conversations(
            empresa_id=tenant.empresa_id,
            limit=limit,
            offset=offset,
            search=search,
            estado=estado,
        )
        return ConversationListResponse(
            items=[
                ConversationResponse.model_validate(ConversationDTO.model_validate(c))
                for c in conversations
            ],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def update_conversation(
        self,
        *,
        tenant: TenantContext,
        conversation_id: UUID,
        payload: ConversationUpdateRequest,
    ) -> ConversationResponse:
        conversation = await self._get_conversation_or_404(
            empresa_id=tenant.empresa_id, conversation_id=conversation_id
        )
        updated = await self._repository.update_conversation(
            conversation=conversation, payload=payload
        )
        await self._repository.commit()
        return ConversationResponse.model_validate(ConversationDTO.model_validate(updated))

    async def delete_conversation(
        self,
        *,
        tenant: TenantContext,
        conversation_id: UUID,
    ) -> None:
        conversation = await self._get_conversation_or_404(
            empresa_id=tenant.empresa_id, conversation_id=conversation_id
        )
        await self._repository.soft_delete_conversation(conversation=conversation)
        await self._repository.commit()

    async def add_message(
        self,
        *,
        tenant: TenantContext,
        conversation_id: UUID,
        payload: MessageCreateRequest,
    ) -> MessageResponse:
        conversation = await self._get_conversation_or_404(
            empresa_id=tenant.empresa_id, conversation_id=conversation_id
        )
        message = await self._repository.add_message(
            empresa_id=tenant.empresa_id,
            conversation_id=conversation.id,
            payload=payload,
        )
        await self._repository.commit()
        return MessageResponse.model_validate(MessageDTO.model_validate(message))

    async def _get_conversation_or_404(
        self, *, empresa_id: UUID, conversation_id: UUID
    ) -> ConversationDTO:
        conversation = await self._repository.get_conversation_by_id(
            empresa_id=empresa_id, conversation_id=conversation_id
        )
        if conversation is None:
            raise AppError(
                code="conversation_not_found",
                message="Conversation not found",
                status_code=404,
            )
        return conversation
