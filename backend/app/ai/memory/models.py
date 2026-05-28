from uuid import UUID

from sqlalchemy import Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TenantMixin, TimestampMixin, UUIDPrimaryKeyMixin


class ConversationMemory(UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "conversation_memories"
    __table_args__ = (
        UniqueConstraint(
            "empresa_id", "customer_id", "memory_type",
            name="uq_memory_tenant_customer_type",
        ),
    )

    customer_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("clientes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("conversations_core.id", ondelete="SET NULL"),
        nullable=True,
    )
    memory_type: Mapped[str] = mapped_column(String(48), nullable=False, default="general")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_preferences: Mapped[list[str] | None] = mapped_column(ARRAY(String(80)), nullable=True)
    extracted_sizes: Mapped[list[str] | None] = mapped_column(ARRAY(String(16)), nullable=True)
    extracted_colors: Mapped[list[str] | None] = mapped_column(ARRAY(String(32)), nullable=True)
    extracted_styles: Mapped[list[str] | None] = mapped_column(ARRAY(String(48)), nullable=True)
    extracted_occasions: Mapped[list[str] | None] = mapped_column(ARRAY(String(48)), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
