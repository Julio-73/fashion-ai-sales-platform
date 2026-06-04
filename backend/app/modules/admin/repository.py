"""Repositorios del módulo Admin (multi-empresa + audit log + admin users)."""
from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.admin.models import (
    ADMIN_AUDIT_ACTIONS,
    DEFAULT_EMPRESA_PLAN,
    DEFAULT_EMPRESA_STATUS,
    AdminAuditLog,
    AdminRefreshToken,
    AdminUser,
)
from app.modules.companies.models import Empresa


# ─────────────────────────────────────────────────────────────────────────────
# AdminUserRepository
# ─────────────────────────────────────────────────────────────────────────────


class AdminUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, *, email: str) -> AdminUser | None:
        result = await self._session.execute(
            select(AdminUser).where(AdminUser.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, *, user_id: UUID) -> AdminUser | None:
        result = await self._session.execute(select(AdminUser).where(AdminUser.id == user_id))
        return result.scalar_one_or_none()

    async def list_all(self, *, limit: int, offset: int) -> tuple[Sequence[AdminUser], int]:
        count = await self._session.execute(select(func.count()).select_from(AdminUser))
        total = int(count.scalar_one())
        result = await self._session.execute(
            select(AdminUser).order_by(AdminUser.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all()), total

    async def create(
        self,
        *,
        email: str,
        password_hash: str,
        rol: str,
        full_name: str | None = None,
    ) -> AdminUser:
        user = AdminUser(
            email=email.lower(),
            password_hash=password_hash,
            rol=rol,
            full_name=full_name,
            is_active=True,
        )
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def update_last_login(self, *, user: AdminUser) -> None:
        user.last_login_at = datetime.now(UTC)
        await self._session.flush()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()


# ─────────────────────────────────────────────────────────────────────────────
# AdminRefreshTokenRepository
# ─────────────────────────────────────────────────────────────────────────────


class AdminRefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        admin_user_id: UUID,
        token_hash: str,
        family_id: UUID,
        expires_at: datetime,
    ) -> AdminRefreshToken:
        record = AdminRefreshToken(
            admin_user_id=admin_user_id,
            token_hash=token_hash,
            family_id=family_id,
            expires_at=expires_at,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_active(self, *, token_hash: str) -> AdminRefreshToken | None:
        result = await self._session.execute(
            select(AdminRefreshToken).where(
                AdminRefreshToken.token_hash == token_hash,
                AdminRefreshToken.revoked_at.is_(None),
                AdminRefreshToken.expires_at > datetime.now(UTC),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_hash(self, *, token_hash: str) -> AdminRefreshToken | None:
        result = await self._session.execute(
            select(AdminRefreshToken).where(AdminRefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def revoke(self, *, token: AdminRefreshToken, replaced_by: UUID | None = None) -> None:
        token.revoked_at = datetime.now(UTC)
        token.replaced_by_token_id = replaced_by
        await self._session.flush()

    async def revoke_family(self, *, family_id: UUID) -> None:
        result = await self._session.execute(
            select(AdminRefreshToken).where(
                AdminRefreshToken.family_id == family_id,
                AdminRefreshToken.revoked_at.is_(None),
            )
        )
        now = datetime.now(UTC)
        for token in result.scalars().all():
            token.revoked_at = now
        await self._session.flush()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()


# ─────────────────────────────────────────────────────────────────────────────
# EmpresaAdminRepository — extiende la consulta de Empresa para super admin
# ─────────────────────────────────────────────────────────────────────────────


class EmpresaAdminRepository:
    """Operaciones cross-tenant sobre ``empresas`` (status / plan / auditoría)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, *, empresa_id: UUID) -> Empresa | None:
        result = await self._session.execute(
            select(Empresa).where(Empresa.id == empresa_id)
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        *,
        limit: int,
        offset: int,
        search: str | None = None,
        status: str | None = None,
        plan: str | None = None,
    ) -> tuple[Sequence[Empresa], int]:
        query = select(Empresa)
        if search:
            pattern = f"%{search.strip()}%"
            query = query.where(or_(Empresa.nombre.ilike(pattern), Empresa.slug.ilike(pattern)))
        if status:
            query = query.where(Empresa.estado == status)
        if plan:
            query = query.where(Empresa.plan == plan)

        count = await self._session.execute(select(func.count()).select_from(query.subquery()))
        total = int(count.scalar_one())
        result = await self._session.execute(
            query.order_by(Empresa.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all()), total

    async def count_by_status(self) -> dict[str, int]:
        result = await self._session.execute(
            select(Empresa.estado, func.count()).group_by(Empresa.estado)
        )
        return {row[0]: int(row[1]) for row in result.all()}

    async def count_by_plan(self) -> dict[str, int]:
        result = await self._session.execute(
            select(Empresa.plan, func.count()).group_by(Empresa.plan)
        )
        return {row[0]: int(row[1]) for row in result.all()}

    async def update_status(self, *, empresa: Empresa, status: str) -> Empresa:
        empresa.estado = status
        await self._session.flush()
        return empresa

    async def update_plan(self, *, empresa: Empresa, plan: str) -> Empresa:
        empresa.plan = plan
        await self._session.flush()
        return empresa

    async def update_fields(
        self,
        *,
        empresa: Empresa,
        nombre: str | None = None,
        plan: str | None = None,
        logo_url: str | None = None,
        status: str | None = None,
    ) -> Empresa:
        if nombre is not None:
            empresa.nombre = nombre
        if plan is not None:
            empresa.plan = plan
        if logo_url is not None:
            empresa.logo_url = logo_url
        if status is not None:
            empresa.estado = status
        await self._session.flush()
        return empresa

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()


# ─────────────────────────────────────────────────────────────────────────────
# AdminAuditRepository
# ─────────────────────────────────────────────────────────────────────────────


class AdminAuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        *,
        admin_user_id: UUID,
        action: str,
        target_empresa_id: UUID | None = None,
        details: dict | None = None,
        ip_address: str | None = None,
    ) -> AdminAuditLog:
        if action not in ADMIN_AUDIT_ACTIONS:
            raise ValueError(f"Unsupported admin audit action: {action}")
        # ``AdminAuditLog.details`` is a JSONB column; SQLAlchemy handles the
        # JSON (de)serialization, so we pass the dict through directly.
        entry = AdminAuditLog(
            admin_user_id=admin_user_id,
            target_empresa_id=target_empresa_id,
            action=action,
            details=details,
            ip_address=ip_address,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        action: str | None = None,
        admin_user_id: UUID | None = None,
        target_empresa_id: UUID | None = None,
    ) -> tuple[Sequence[AdminAuditLog], int]:
        query = select(AdminAuditLog)
        if action:
            query = query.where(AdminAuditLog.action == action)
        if admin_user_id:
            query = query.where(AdminAuditLog.admin_user_id == admin_user_id)
        if target_empresa_id:
            query = query.where(AdminAuditLog.target_empresa_id == target_empresa_id)

        count = await self._session.execute(select(func.count()).select_from(query.subquery()))
        total = int(count.scalar_one())
        result = await self._session.execute(
            query.order_by(AdminAuditLog.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all()), total

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()


# ─────────────────────────────────────────────────────────────────────────────
# GlobalMetricsRepository — agregaciones cross-tenant
# ─────────────────────────────────────────────────────────────────────────────


class GlobalMetricsRepository:
    """Conteos agregados a través de TODAS las empresas.

    Usa ``func.count()`` con ``text()`` para evitar importar los modelos
    de los módulos congelados. Mantiene este módulo 100% aditivo.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def total_clientes(self) -> int:
        from sqlalchemy import text

        result = await self._session.execute(text("SELECT count(*) FROM clientes"))
        return int(result.scalar_one())

    async def total_pedidos(self) -> int:
        from sqlalchemy import text

        result = await self._session.execute(text("SELECT count(*) FROM orders"))
        return int(result.scalar_one())

    async def total_conversaciones(self) -> int:
        from sqlalchemy import text

        result = await self._session.execute(text("SELECT count(*) FROM conversations"))
        return int(result.scalar_one())

    async def total_ventas(self) -> float:
        from sqlalchemy import text

        result = await self._session.execute(
            text("SELECT COALESCE(SUM(total), 0) FROM orders WHERE status = 'confirmed'")
        )
        value = result.scalar_one()
        return float(value or 0)


__all__ = [
    "AdminAuditRepository",
    "AdminRefreshTokenRepository",
    "AdminUserRepository",
    "EmpresaAdminRepository",
    "GlobalMetricsRepository",
]
