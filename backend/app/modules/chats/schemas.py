from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ChatResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    cliente_id: UUID | None
    canal: str
    estado: str

    model_config = ConfigDict(from_attributes=True)

