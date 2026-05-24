from uuid import UUID

from pydantic import BaseModel


class CompanyDTO(BaseModel):
    id: UUID
    nombre: str
    slug: str

