from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AnalyticsEventResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    nombre_evento: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

