from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.conversations.models import ConversationCore
from app.conversations.schemas import (
    AddMessageCoreResponse,
    ConversationCoreCreateRequest,
    ConversationCoreDetailResponse,
    ConversationCoreListResponse,
    ConversationCoreResponse,
    MessageCoreCreateRequest,
    MessageCoreListResponse,
    MessageCoreResponse,
)
from app.conversations.repository import ConversationCoreRepository
from app.core.errors import AppError
from app.core.security.dependencies import TenantContext
from app.services.crm_bridge import CrmBridgeService


class ConversationCoreService:
    def __init__(
        self,
        repository: ConversationCoreRepository,
        crm_bridge: CrmBridgeService | None = None,
        ai_reply_service=None,
    ) -> None:
        self._repository = repository
        self._crm_bridge = crm_bridge
        self._ai_reply_service = ai_reply_service

    async def create_conversation(
        self,
        *,
        tenant: TenantContext,
        payload: ConversationCoreCreateRequest,
    ) -> ConversationCoreResponse:
        try:
            conversation = await self._repository.create_conversation(
                empresa_id=tenant.empresa_id, payload=payload
            )
            if self._crm_bridge and conversation.customer_id:
                await self._crm_bridge.increment_conversation_count(
                    empresa_id=tenant.empresa_id,
                    customer_id=conversation.customer_id,
                )
            await self._repository.commit()
            return ConversationCoreResponse.model_validate(conversation)
        except IntegrityError as exc:
            await self._repository.rollback()
            raise AppError(code="conversation_conflict", message="Failed to create conversation", status_code=409) from exc

    async def get_conversation(
        self,
        *,
        tenant: TenantContext,
        conversation_id: UUID,
    ) -> ConversationCoreDetailResponse:
        conversation = await self._get_conversation_or_404(
            empresa_id=tenant.empresa_id, conversation_id=conversation_id
        )
        messages, _ = await self._repository.list_messages(
            empresa_id=tenant.empresa_id,
            conversation_id=conversation_id,
            limit=200,
            offset=0,
        )
        return ConversationCoreDetailResponse(
            **ConversationCoreResponse.model_validate(conversation).model_dump(),
            messages=[MessageCoreResponse.model_validate(m) for m in messages],
        )

    async def list_conversations(
        self,
        *,
        tenant: TenantContext,
        limit: int,
        offset: int,
        search: str | None,
        status: str | None,
    ) -> ConversationCoreListResponse:
        conversations, total = await self._repository.list_conversations(
            empresa_id=tenant.empresa_id,
            limit=limit,
            offset=offset,
            search=search,
            status=status,
        )
        return ConversationCoreListResponse(
            items=[ConversationCoreResponse.model_validate(c) for c in conversations],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def update_conversation(
        self,
        *,
        tenant: TenantContext,
        conversation_id: UUID,
        status: str | None,
    ) -> ConversationCoreResponse:
        conversation = await self._get_conversation_or_404(
            empresa_id=tenant.empresa_id, conversation_id=conversation_id
        )
        updated = await self._repository.update_conversation(
            conversation=conversation, status=status
        )
        if self._crm_bridge and conversation.customer_id and status:
            await self._crm_bridge.sync_conversation_status(
                empresa_id=tenant.empresa_id,
                customer_id=conversation.customer_id,
                conversation_status=status,
            )
        await self._repository.commit()
        return ConversationCoreResponse.model_validate(updated)

    async def delete_conversation(
        self,
        *,
        tenant: TenantContext,
        conversation_id: UUID,
    ) -> None:
        conversation = await self._get_conversation_or_404(
            empresa_id=tenant.empresa_id, conversation_id=conversation_id
        )
        await self._repository.delete_conversation(conversation=conversation)
        await self._repository.commit()

    async def add_message(
        self,
        *,
        tenant: TenantContext,
        conversation_id: UUID,
        payload: MessageCoreCreateRequest,
    ) -> AddMessageCoreResponse:
        conversation = await self._get_conversation_or_404(
            empresa_id=tenant.empresa_id, conversation_id=conversation_id
        )
        message = await self._repository.add_message(
            empresa_id=tenant.empresa_id,
            conversation_id=conversation.id,
            payload=payload,
        )
        await self._repository.update_last_message(
            conversation=conversation, content=payload.content
        )

        if self._crm_bridge and conversation.customer_id:
            sync_result = await self._crm_bridge.sync_after_message(
                empresa_id=tenant.empresa_id,
                customer_id=conversation.customer_id,
                conversation_id=conversation.id,
                conversation_status=conversation.status,
                message_content=payload.content,
                message_sender=payload.sender,
            )
            if sync_result.should_reactivate:
                conversation.status = "active"

        ai_reply = None
        if self._ai_reply_service and payload.sender in ("user", "client"):
            should = await self._ai_reply_service.should_auto_reply(
                empresa_id=tenant.empresa_id,
                conversation_id=conversation.id,
                sender=payload.sender,
                status=conversation.status,
            )
            if should:
                ai_msg = await self._ai_reply_service.generate_and_save_ai_reply(
                    empresa_id=tenant.empresa_id,
                    conversation_id=conversation.id,
                    user_message=payload.content,
                )
                if ai_msg:
                    ai_reply = MessageCoreResponse.model_validate(ai_msg)
                    if ai_msg.content:
                        await self._repository.update_last_message(
                            conversation=conversation, content=ai_msg.content
                        )

        await self._repository.commit()
        return AddMessageCoreResponse(
            message=MessageCoreResponse.model_validate(message),
            ai_reply=ai_reply,
        )

    async def list_messages(
        self,
        *,
        tenant: TenantContext,
        conversation_id: UUID,
        limit: int,
        offset: int,
    ) -> MessageCoreListResponse:
        await self._get_conversation_or_404(
            empresa_id=tenant.empresa_id, conversation_id=conversation_id
        )
        messages, total = await self._repository.list_messages(
            empresa_id=tenant.empresa_id,
            conversation_id=conversation_id,
            limit=limit,
            offset=offset,
        )
        return MessageCoreListResponse(
            items=[MessageCoreResponse.model_validate(m) for m in messages],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def _get_conversation_or_404(
        self, *, empresa_id: UUID, conversation_id: UUID
    ) -> ConversationCore:
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
