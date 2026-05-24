from uuid import UUID

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TenantMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Chat(UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "chats"
    __table_args__ = (Index("idx_chats__empresa_id_estado_updated_at", "empresa_id", "estado", "updated_at"),)

    cliente_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("clientes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    canal: Mapped[str] = mapped_column(String(32), nullable=False, default="manual")
    estado: Mapped[str] = mapped_column(String(32), nullable=False, default="open")

