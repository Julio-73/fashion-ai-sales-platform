import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.context.repositories.sales_context_repository import (
    SalesContextRepository,
)
from app.ai.schemas.ai_schemas import SalesContextDetail

logger = logging.getLogger("ai_sales_agent.ai.context.services.behavioral")


class BehavioralProfileService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = SalesContextRepository(session)

    async def build_sales_context(
        self, *, empresa_id: UUID, customer_id: UUID
    ) -> SalesContextDetail:
        is_hot = await self._repo.is_hot_lead(
            empresa_id=empresa_id, customer_id=customer_id
        )
        is_premium = await self._repo.is_premium_customer(
            empresa_id=empresa_id, customer_id=customer_id
        )
        evolution = await self._repo.get_lead_score_evolution(
            empresa_id=empresa_id, customer_id=customer_id
        )

        return SalesContextDetail(
            conversion_probability=await self._repo.get_conversion_probability(
                empresa_id=empresa_id, customer_id=customer_id
            ),
            negotiation_stage=await self._repo.get_negotiation_stage(
                empresa_id=empresa_id, customer_id=customer_id
            ),
            discount_sensitivity=await self._repo.get_discount_sensitivity(
                empresa_id=empresa_id, customer_id=customer_id
            ),
            buying_intent_trend=await self._repo.get_buying_intent_trend(
                empresa_id=empresa_id, customer_id=customer_id
            ),
            lead_score_evolution=evolution,
            churn_risk=await self._repo.get_churn_risk(
                empresa_id=empresa_id, customer_id=customer_id
            ),
            is_hot_lead=is_hot,
            is_premium_customer=is_premium,
        )
