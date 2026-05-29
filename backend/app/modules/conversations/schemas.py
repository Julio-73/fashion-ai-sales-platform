from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ConversationStatus = Literal["open", "pending", "closed"]
ConversationChannel = Literal["manual", "whatsapp", "instagram", "facebook", "web"]
MessageRole = Literal["agent", "client", "system"]


class ConversationCreateRequest(BaseModel):
    cliente_id: UUID | None = None
    asunto: str | None = Field(default=None, max_length=240)
    canal: ConversationChannel = "manual"


class ConversationUpdateRequest(BaseModel):
    asunto: str | None = Field(default=None, max_length=240)
    canal: ConversationChannel | None = None
    estado: ConversationStatus | None = None


class MessageCreateRequest(BaseModel):
    role: MessageRole
    content: str = Field(min_length=1, max_length=10000)
    sender_name: str | None = Field(default=None, max_length=160)
    extra_data: dict[str, Any] | None = None


class MessageResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    conversation_id: UUID
    role: MessageRole
    content: str
    sender_name: str | None
    extra_data: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    cliente_id: UUID | None
    asunto: str | None
    canal: ConversationChannel
    estado: ConversationStatus
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationDetailResponse(ConversationResponse):
    messages: list[MessageResponse] = []


class ConversationListResponse(BaseModel):
    items: list[ConversationResponse]
    total: int
    limit: int
    offset: int


class ProcessMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=10000)
    role: MessageRole = "client"
    sender_name: str | None = Field(default=None, max_length=160)


class TypingState(BaseModel):
    is_typing: bool


class ProcessMessageResponse(BaseModel):
    message: MessageResponse
    ai_reply: MessageResponse | None = None
    typing: TypingState


class RegenerateRequest(BaseModel):
    conversation_id: UUID | None = None
