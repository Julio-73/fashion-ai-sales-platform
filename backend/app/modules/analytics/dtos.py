from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AnalyticsEventDTO(BaseModel):
    id: UUID
    empresa_id: UUID
    nombre_evento: str
    created_at: datetime

