from uuid import UUID

from pydantic import BaseModel


class ChatDTO(BaseModel):
    id: UUID
    empresa_id: UUID
    cliente_id: UUID | None = None
    estado: str

