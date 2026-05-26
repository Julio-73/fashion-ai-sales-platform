from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TenantMixin, TimestampMixin, UUIDPrimaryKeyMixin

LEAD_STATUS_VALUES = ("new", "interested", "negotiating", "won", "lost")


class Cliente(UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "clientes"
    __table_args__ = (
        UniqueConstraint("empresa_id", "email", name="uq_clientes__empresa_id_email"),
        Index("idx_clientes__empresa_id_created_at", "empresa_id", "created_at"),
        Index("idx_clientes__empresa_id_lead_status_created_at", "empresa_id", "lead_status", "created_at"),
        Index("idx_clientes__empresa_id_full_name", "empresa_id", "full_name"),
        Index("idx_clientes__empresa_id_last_interaction_at", "empresa_id", "last_interaction_at"),
        CheckConstraint(
            "lead_status in ('new', 'interested', 'negotiating', 'won', 'lost')",
            name="ck_clientes__lead_status",
        ),
    )

    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    whatsapp: Mapped[str | None] = mapped_column(String(32), nullable=True)
    instagram_username: Mapped[str | None] = mapped_column(String(80), nullable=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String(48)), nullable=False, default=list)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    lead_status: Mapped[str] = mapped_column(String(32), nullable=False, default="new")
    source: Mapped[str | None] = mapped_column(String(80), nullable=True)
    assigned_to: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    last_interaction_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    conversation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    last_conversation_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("conversations_core.id", ondelete="SET NULL"),
        nullable=True,
    )
    lead_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    priority: Mapped[str] = mapped_column(String(16), nullable=False, default="cold", server_default="cold")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

