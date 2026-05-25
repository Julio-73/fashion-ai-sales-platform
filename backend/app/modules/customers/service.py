import logging

from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.core.errors import AppError
from app.core.security.dependencies import TenantContext
from app.modules.customers.dtos import CustomerDTO
from app.modules.customers.repository import CustomerRepository
from app.modules.customers.schemas import (
    CustomerCreateRequest,
    CustomerListResponse,
    CustomerResponse,
    CustomerUpdateRequest,
    LeadStatus,
)

logger = logging.getLogger("ai_sales_agent.customers")


def _sanitize_tags(tags: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for tag in tags:
        cleaned = tag.strip()[:48]
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result


class CustomerService:
    def __init__(self, repository: CustomerRepository) -> None:
        self._repository = repository

    async def create_customer(
        self,
        *,
        tenant: TenantContext,
        payload: CustomerCreateRequest,
    ) -> CustomerResponse:
        name = payload.full_name.strip()
        if not name:
            raise AppError(code="invalid_input", message="Full name cannot be empty", status_code=422)
        sanitized = payload.model_copy(update={
            "full_name": name,
            "tags": _sanitize_tags(payload.tags),
        })
        try:
            customer = await self._repository.create(empresa_id=tenant.empresa_id, payload=sanitized)
            await self._repository.commit()
            return CustomerResponse.model_validate(CustomerDTO.model_validate(customer))
        except IntegrityError as exc:
            await self._repository.rollback()
            raise AppError(code="customer_conflict", message="Customer already exists", status_code=409) from exc

    async def get_customer(self, *, tenant: TenantContext, customer_id: UUID) -> CustomerResponse:
        customer = await self._get_customer_or_404(empresa_id=tenant.empresa_id, customer_id=customer_id)
        return CustomerResponse.model_validate(CustomerDTO.model_validate(customer))

    async def list_customers(
        self,
        *,
        tenant: TenantContext,
        limit: int,
        offset: int,
        search: str | None,
        lead_status: LeadStatus | None,
    ) -> CustomerListResponse:
        logger.info(
            "list_customers empresa=%s limit=%s offset=%s search=%s lead_status=%s",
            tenant.empresa_id, limit, offset, search, lead_status,
        )
        customers, total = await self._repository.list(
            empresa_id=tenant.empresa_id,
            limit=limit,
            offset=offset,
            search=search,
            lead_status=lead_status,
        )
        logger.info("list_customers result total=%s returned=%s", total, len(customers))
        return CustomerListResponse(
            items=[CustomerResponse.model_validate(CustomerDTO.model_validate(customer)) for customer in customers],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def update_customer(
        self,
        *,
        tenant: TenantContext,
        customer_id: UUID,
        payload: CustomerUpdateRequest,
    ) -> CustomerResponse:
        customer = await self._get_customer_or_404(empresa_id=tenant.empresa_id, customer_id=customer_id)
        dump = payload.model_dump(exclude_unset=True)
        if "full_name" in dump:
            name = dump["full_name"].strip()
            if not name:
                raise AppError(code="invalid_input", message="Full name cannot be empty", status_code=422)
            dump["full_name"] = name
        if "tags" in dump and dump["tags"] is not None:
            dump["tags"] = _sanitize_tags(dump["tags"])
        try:
            updated = await self._repository.update(customer=customer, payload=dump)
            await self._repository.commit()
            return CustomerResponse.model_validate(CustomerDTO.model_validate(updated))
        except IntegrityError as exc:
            await self._repository.rollback()
            raise AppError(code="customer_conflict", message="Customer update conflicts", status_code=409) from exc

    async def delete_customer(self, *, tenant: TenantContext, customer_id: UUID) -> None:
        customer = await self._get_customer_or_404(empresa_id=tenant.empresa_id, customer_id=customer_id)
        await self._repository.soft_delete(customer=customer)
        await self._repository.commit()

    async def _get_customer_or_404(self, *, empresa_id: UUID, customer_id: UUID):
        customer = await self._repository.get_by_id(empresa_id=empresa_id, customer_id=customer_id)
        if customer is None:
            raise AppError(code="customer_not_found", message="Customer not found", status_code=404)
        return customer

