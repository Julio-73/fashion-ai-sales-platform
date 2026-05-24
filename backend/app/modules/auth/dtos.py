from uuid import UUID

from pydantic import BaseModel, EmailStr


class AuthenticatedUserDTO(BaseModel):
    id: UUID
    empresa_id: UUID
    email: EmailStr
    roles: list[str]
    permissions: list[str]

