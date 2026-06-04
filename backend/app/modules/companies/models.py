from sqlalchemy import CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Empresa(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "empresas"
    __table_args__ = (
        CheckConstraint(
            "estado in ('active', 'suspended', 'expired')",
            name="ck_empresas__estado",
        ),
        CheckConstraint(
            "plan in ('basic', 'pro', 'enterprise')",
            name="ck_empresas__plan",
        ),
    )

    nombre: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    estado: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    plan: Mapped[str] = mapped_column(
        String(32), nullable=False, default="basic", server_default="basic"
    )
    logo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
