from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ConversationCoreStatus = Literal["active", "closed", "converted"]
MessageCoreSender = Literal["user", "bot", "system"]


class ConversationCoreCreateRequest(BaseModel):
    customer_id: UUID | None = None
    status: ConversationCoreStatus = "active"


class ConversationCoreUpdateRequest(BaseModel):
    status: ConversationCoreStatus | None = None


class MessageCoreCreateRequest(BaseModel):
    sender: MessageCoreSender
    content: str = Field(min_length=1, max_length=10000)


class MessageCoreResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    conversation_id: UUID
    sender: str
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationCoreResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    customer_id: UUID | None
    status: str
    last_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationCoreDetailResponse(ConversationCoreResponse):
    messages: list[MessageCoreResponse] = []


class ConversationCoreListResponse(BaseModel):
    items: list[ConversationCoreResponse]
    total: int
    limit: int
    offset: int


class MessageCoreListResponse(BaseModel):
    items: list[MessageCoreResponse]
    total: int
    limit: int
    offset: int


class AddMessageCoreResponse(BaseModel):
    message: MessageCoreResponse
    ai_reply: MessageCoreResponse | None = None
