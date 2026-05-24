from sqlalchemy import Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TenantMixin, TimestampMixin, UUIDPrimaryKeyMixin


class AnalyticsEvent(UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "eventos_analytics"
    __table_args__ = (
        Index("idx_eventos_analytics__empresa_id_nombre_evento_created_at", "empresa_id", "nombre_evento", "created_at"),
    )

    nombre_evento: Mapped[str] = mapped_column(String(120), nullable=False)
    entidad_tipo: Mapped[str | None] = mapped_column(String(80), nullable=True)
    entidad_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    source: Mapped[str] = mapped_column(String(80), nullable=False, default="app")
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

