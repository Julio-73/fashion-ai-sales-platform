from uuid import UUID

from sqlalchemy import Boolean, Float, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TenantMixin, TimestampMixin, UUIDPrimaryKeyMixin


class ConversationAIState(UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "conversation_ai_states"
    __table_args__ = (
        Index("idx_ai_state__empresa_conversation", "empresa_id", "conversation_id"),
        UniqueConstraint("empresa_id", "conversation_id", name="uq_ai_state_tenant_conversation"),
    )

    conversation_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("conversations_core.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ai_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    auto_reply_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    escalation_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_detected_intent: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String(32), nullable=True)
    urgency_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    lead_temperature: Mapped[str | None] = mapped_column(String(16), nullable=True)
    ai_last_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)


class ConversationAIEvent(UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "conversation_ai_events"
    __table_args__ = (
        Index("idx_ai_event__empresa_conversation", "empresa_id", "conversation_id"),
        Index("idx_ai_event__created_at", "created_at"),
    )

    conversation_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("conversations_core.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(48), nullable=False)
    payload: Mapped[str | None] = mapped_column(Text, nullable=True)
