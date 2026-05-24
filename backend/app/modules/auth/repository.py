from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import EmpresaUsuario, RefreshToken, Usuario
from app.modules.companies.models import Empresa


class AuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_user_by_email(self, *, email: str) -> Usuario | None:
        result = await self._session.execute(select(Usuario).where(Usuario.email == email))
        return result.scalar_one_or_none()

    async def create_company_with_owner(
        self,
        *,
        company_name: str,
        company_slug: str,
        email: str,
        password_hash: str,
    ) -> tuple[Empresa, Usuario, EmpresaUsuario]:
        company = Empresa(nombre=company_name, slug=company_slug, estado="active")
        user = Usuario(email=email, password_hash=password_hash, estado="active")
        self._session.add_all([company, user])
        await self._session.flush()

        membership = EmpresaUsuario(
            empresa_id=company.id,
            usuario_id=user.id,
            rol="owner",
            estado="active",
        )
        self._session.add(membership)
        await self._session.flush()
        return company, user, membership

    async def get_membership(
        self,
        *,
        empresa_id: UUID,
        usuario_id: UUID,
    ) -> EmpresaUsuario | None:
        result = await self._session.execute(
            select(EmpresaUsuario).where(
                EmpresaUsuario.empresa_id == empresa_id,
                EmpresaUsuario.usuario_id == usuario_id,
                EmpresaUsuario.estado == "active",
            )
        )
        return result.scalar_one_or_none()

    async def list_active_memberships(self, *, usuario_id: UUID) -> list[EmpresaUsuario]:
        result = await self._session.execute(
            select(EmpresaUsuario).where(
                EmpresaUsuario.usuario_id == usuario_id,
                EmpresaUsuario.estado == "active",
            )
        )
        return list(result.scalars().all())

    async def create_refresh_token(
        self,
        *,
        empresa_id: UUID,
        usuario_id: UUID,
        token_hash: str,
        family_id: UUID,
        expires_at: datetime,
    ) -> RefreshToken:
        refresh_token = RefreshToken(
            empresa_id=empresa_id,
            usuario_id=usuario_id,
            token_hash=token_hash,
            family_id=family_id,
            expires_at=expires_at,
        )
        self._session.add(refresh_token)
        await self._session.flush()
        return refresh_token

    async def get_active_refresh_token(self, *, token_hash: str) -> RefreshToken | None:
        result = await self._session.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > datetime.now(UTC),
            )
        )
        return result.scalar_one_or_none()

    async def get_refresh_token_by_hash(self, *, token_hash: str) -> RefreshToken | None:
        result = await self._session.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
        return result.scalar_one_or_none()

    async def revoke_refresh_token(
        self,
        *,
        refresh_token: RefreshToken,
        replaced_by_token_id: UUID | None = None,
    ) -> None:
        refresh_token.revoked_at = datetime.now(UTC)
        refresh_token.replaced_by_token_id = replaced_by_token_id
        await self._session.flush()

    async def revoke_refresh_token_family(self, *, family_id: UUID) -> None:
        result = await self._session.execute(
            select(RefreshToken).where(
                RefreshToken.family_id == family_id,
                RefreshToken.revoked_at.is_(None),
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

