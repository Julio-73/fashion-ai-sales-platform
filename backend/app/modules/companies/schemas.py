from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CompanyResponse(BaseModel):
    id: UUID
    nombre: str = Field(min_length=1, max_length=160)
    slug: str

    model_config = ConfigDict(from_attributes=True)

