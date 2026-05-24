from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ConversationDTO(BaseModel):
    id: UUID
    empresa_id: UUID
    cliente_id: UUID | None
    asunto: str | None
    canal: str
    estado: str
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageDTO(BaseModel):
    id: UUID
    empresa_id: UUID
    conversation_id: UUID
    role: str
    content: str
    sender_name: str | None
    extra_data: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
