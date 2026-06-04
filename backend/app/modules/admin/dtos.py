"""DTOs internos del módulo Admin (separados de ``schemas`` por convención)."""
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, EmailStr


class AdminUserDTO(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str | None = None
    rol: str
    is_active: bool
    last_login_at: str | None = None
