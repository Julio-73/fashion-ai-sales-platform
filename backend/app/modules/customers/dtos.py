from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

LeadStatus = Literal["new", "interested", "negotiating", "won", "lost"]


class CustomerDTO(BaseModel):
    id: UUID
    empresa_id: UUID
    full_name: str
    email: EmailStr | None
    phone: str | None
    whatsapp: str | None
    instagram_username: str | None
    tags: list[str]
    notes: str | None
    lead_status: LeadStatus
    source: str | None
    assigned_to: UUID | None
    last_interaction_at: datetime | None = None
    conversation_count: int = 0
    last_conversation_id: UUID | None = None
    lead_score: int = 0
    priority: str = "cold"
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

