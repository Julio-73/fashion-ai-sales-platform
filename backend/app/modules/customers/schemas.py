from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

LeadStatus = Literal["new", "interested", "negotiating", "won", "lost"]

_TAG_MAX_LENGTH = 48  # matches ARRAY(String(48)) in the model


class CustomerCreateRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=160)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, min_length=6, max_length=32)
    whatsapp: str | None = Field(default=None, min_length=6, max_length=32)
    instagram_username: str | None = Field(default=None, min_length=1, max_length=80)
    tags: list[str] = Field(default_factory=list, max_length=20)
    notes: str | None = Field(default=None, max_length=4000)
    lead_status: LeadStatus = "new"
    source: str | None = Field(default=None, max_length=80)
    assigned_to: UUID | None = None

    @field_validator("tags")
    @classmethod
    def _validate_tag_lengths(cls, tags: list[str]) -> list[str]:
        for tag in tags:
            stripped = tag.strip()
            if not stripped:
                raise ValueError("Tags cannot be empty")
            if len(stripped) > _TAG_MAX_LENGTH:
                raise ValueError(f"Tag exceeds maximum length of {_TAG_MAX_LENGTH} characters")
        return tags


class CustomerUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=160)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, min_length=6, max_length=32)
    whatsapp: str | None = Field(default=None, min_length=6, max_length=32)
    instagram_username: str | None = Field(default=None, min_length=1, max_length=80)
    tags: list[str] | None = Field(default=None, max_length=20)
    notes: str | None = Field(default=None, max_length=4000)
    lead_status: LeadStatus | None = None
    source: str | None = Field(default=None, max_length=80)
    assigned_to: UUID | None = None

    @field_validator("tags")
    @classmethod
    def _validate_tag_lengths(cls, tags: list[str] | None) -> list[str] | None:
        if tags is None:
            return None
        for tag in tags:
            stripped = tag.strip()
            if not stripped:
                raise ValueError("Tags cannot be empty")
            if len(stripped) > _TAG_MAX_LENGTH:
                raise ValueError(f"Tag exceeds maximum length of {_TAG_MAX_LENGTH} characters")
        return tags


class CustomerResponse(BaseModel):
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
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomerListResponse(BaseModel):
    items: list[CustomerResponse]
    total: int
    limit: int
    offset: int

