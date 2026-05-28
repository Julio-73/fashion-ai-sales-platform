import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.context.repositories.customer_context_repository import (
    CustomerContextRepository,
)
from app.ai.schemas.ai_schemas import RichCustomerProfile

logger = logging.getLogger("ai_sales_agent.ai.context.services.customer_memory")


class CustomerMemoryService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CustomerContextRepository(session)

    async def build_profile(
        self, *, empresa_id: UUID, customer_id: UUID
    ) -> RichCustomerProfile:
        customer = await self._repo.get_customer(
            empresa_id=empresa_id, customer_id=customer_id
        )
        if customer is None:
            return RichCustomerProfile(customer_id=customer_id, full_name="")

        total_conversations = await self._repo.get_customer_interaction_count(
            empresa_id=empresa_id, customer_id=customer_id
        )
        purchase_summary = await self._repo.get_purchase_history_summary(
            empresa_id=empresa_id, customer_id=customer_id
        )
        preferred = await self._repo.get_preferred_attributes(
            empresa_id=empresa_id, customer_id=customer_id
        )
        favorite_categories = await self._repo.get_favorite_categories(
            empresa_id=empresa_id, customer_id=customer_id
        )
        lead_evolution = await self._repo.get_lead_score_evolution(
            empresa_id=empresa_id, customer_id=customer_id
        )
        tags = customer.tags or []
        is_vip = any(t.lower() in ("vip", "premium", "recurrente") for t in tags)

        return RichCustomerProfile(
            customer_id=customer.id,
            full_name=customer.full_name,
            email=customer.email,
            phone=customer.phone,
            tags=tags,
            lead_score=float(customer.lead_score or 0),
            lead_status=customer.lead_status,
            priority=customer.priority or "cold",
            total_conversations=total_conversations,
            last_interaction_at=customer.last_interaction_at,
            favorite_categories=favorite_categories,
            preferred_colors=preferred.get("colors", []),
            preferred_sizes=preferred.get("sizes", []),
            average_order_value=purchase_summary["avg_order_value"],
            customer_lifetime_value=purchase_summary["total_lifetime_value"],
            is_vip=is_vip,
            detected_preferences={
                "colors": ", ".join(preferred.get("colors", [])),
                "sizes": ", ".join(preferred.get("sizes", [])),
                "categories": ", ".join(favorite_categories),
            },
        )

    async def get_customer_tags(
        self, *, empresa_id: UUID, customer_id: UUID
    ) -> list[str]:
        return await self._repo.get_customer_tags(
            empresa_id=empresa_id, customer_id=customer_id
        )
