from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.customers.models import Cliente
from app.modules.customers.schemas import CustomerCreateRequest, CustomerUpdateRequest, LeadStatus


class CustomerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, empresa_id: UUID, payload: CustomerCreateRequest) -> Cliente:
        customer = Cliente(empresa_id=empresa_id, **payload.model_dump())
        self._session.add(customer)
        await self._session.flush()
        return customer

    async def find_by_phone(
        self, *, empresa_id: UUID, phone: str
    ) -> Cliente | None:
        """Return the first customer whose ``phone`` or ``whatsapp``
        column matches ``phone`` (exact match, tenant-scoped).

        Used by the WhatsApp integration to look up the customer
        associated with an incoming message. The two columns are kept
        in sync by the API; we check both to be robust to historical
        data inconsistencies.
        """
        if not phone:
            return None
        result = await self._session.execute(
            select(Cliente)
            .where(
                Cliente.empresa_id == empresa_id,
                Cliente.deleted_at.is_(None),
                or_(Cliente.phone == phone, Cliente.whatsapp == phone),
            )
            .order_by(Cliente.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, *, empresa_id: UUID, customer_id: UUID) -> Cliente | None:
        result = await self._session.execute(
            select(Cliente).where(
                Cliente.empresa_id == empresa_id,
                Cliente.id == customer_id,
                Cliente.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        empresa_id: UUID,
        limit: int,
        offset: int,
        search: str | None = None,
        lead_status: LeadStatus | None = None,
    ) -> tuple[Sequence[Cliente], int]:
        query = self._filtered_query(empresa_id=empresa_id, search=search, lead_status=lead_status)
        count_result = await self._session.execute(select(func.count()).select_from(query.subquery()))
        total = int(count_result.scalar_one())

        result = await self._session.execute(
            query.order_by(Cliente.created_at.desc()).limit(limit).offset(offset)
        )
        return result.scalars().all(), total

    async def update(
        self,
        *,
        customer: Cliente,
        payload: CustomerUpdateRequest | dict,
    ) -> Cliente:
        values = payload.model_dump(exclude_unset=True) if not isinstance(payload, dict) else payload
        for field, value in values.items():
            setattr(customer, field, value)
        customer.updated_at = datetime.now(UTC)
        await self._session.flush()
        return customer

    async def soft_delete(self, *, customer: Cliente) -> None:
        customer.deleted_at = datetime.now(UTC)
        await self._session.flush()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    def _filtered_query(
        self,
        *,
        empresa_id: UUID,
        search: str | None,
        lead_status: LeadStatus | None,
    ) -> Select[tuple[Cliente]]:
        query = select(Cliente).where(
            Cliente.empresa_id == empresa_id,
            Cliente.deleted_at.is_(None),
        )
        if lead_status:
            query = query.where(Cliente.lead_status == lead_status)
        if search:
            pattern = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Cliente.full_name.ilike(pattern),
                    Cliente.email.ilike(pattern),
                    Cliente.phone.ilike(pattern),
                    Cliente.whatsapp.ilike(pattern),
                    Cliente.instagram_username.ilike(pattern),
                )
            )
        return query
