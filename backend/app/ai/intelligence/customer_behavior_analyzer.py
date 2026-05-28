import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.context.repositories.customer_context_repository import (
    CustomerContextRepository,
)
from app.ai.context.repositories.sales_context_repository import (
    SalesContextRepository,
)

logger = logging.getLogger("ai_sales_agent.ai.intelligence.behavior")


class CustomerBehaviorAnalyzer:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._customer_repo = CustomerContextRepository(session)
        self._sales_repo = SalesContextRepository(session)

    async def detect_hot_customers(
        self, *, empresa_id: UUID, customer_ids: list[UUID]
    ) -> list[dict]:
        hot = []
        for cid in customer_ids:
            is_hot = await self._sales_repo.is_hot_lead(
                empresa_id=empresa_id, customer_id=cid
            )
            if is_hot:
                trend = await self._sales_repo.get_buying_intent_trend(
                    empresa_id=empresa_id, customer_id=cid
                )
                prob = await self._sales_repo.get_conversion_probability(
                    empresa_id=empresa_id, customer_id=cid
                )
                hot.append({
                    "customer_id": str(cid),
                    "is_hot": True,
                    "trend": trend,
                    "conversion_probability": prob,
                })
        return hot

    async def detect_increasing_intent(
        self, *, empresa_id: UUID, customer_ids: list[UUID]
    ) -> list[dict]:
        increasing = []
        for cid in customer_ids:
            trend = await self._sales_repo.get_buying_intent_trend(
                empresa_id=empresa_id, customer_id=cid
            )
            if trend == "increasing":
                prob = await self._sales_repo.get_conversion_probability(
                    empresa_id=empresa_id, customer_id=cid
                )
                increasing.append({
                    "customer_id": str(cid),
                    "trend": trend,
                    "conversion_probability": prob,
                })
        return increasing

    async def detect_discount_sensitivity(
        self, *, empresa_id: UUID, customer_ids: list[UUID]
    ) -> list[dict]:
        sensitive = []
        for cid in customer_ids:
            sensitivity = await self._sales_repo.get_discount_sensitivity(
                empresa_id=empresa_id, customer_id=cid
            )
            if sensitivity == "high":
                sensitive.append({
                    "customer_id": str(cid),
                    "discount_sensitivity": sensitivity,
                })
        return sensitive

    async def detect_premium_customers(
        self, *, empresa_id: UUID, customer_ids: list[UUID]
    ) -> list[dict]:
        premium = []
        for cid in customer_ids:
            is_premium = await self._sales_repo.is_premium_customer(
                empresa_id=empresa_id, customer_id=cid
            )
            if is_premium:
                purchase = await self._customer_repo.get_purchase_history_summary(
                    empresa_id=empresa_id, customer_id=cid
                )
                premium.append({
                    "customer_id": str(cid),
                    "is_premium": True,
                    "lifetime_value": purchase.get("total_lifetime_value", 0),
                })
        return premium
