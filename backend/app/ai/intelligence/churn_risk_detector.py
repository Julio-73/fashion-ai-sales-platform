import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.customers.models import Cliente

logger = logging.getLogger("ai_sales_agent.ai.intelligence.churn")


class ChurnRiskDetector:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def evaluate_churn(
        self, *, empresa_id: UUID, customer_id: UUID
    ) -> dict:
        customer = await self._get_customer(empresa_id, customer_id)
        if customer is None:
            return {"risk": "unknown", "factors": []}

        factors = []
        risk_score = 0

        if customer.last_interaction_at:
            last = customer.last_interaction_at
            if last.tzinfo is None:
                last = last.replace(tzinfo=UTC)
            days_since = (datetime.now(UTC) - last).days

            if days_since > 60:
                risk_score += 40
                factors.append(f"Sin interacción en {days_since} días")
            elif days_since > 30:
                risk_score += 20
                factors.append(f"Sin interacción en {days_since} días")
            elif days_since > 14:
                risk_score += 10
                factors.append(f"Sin interacción en {days_since} días")
        else:
            risk_score += 30
            factors.append("Nunca ha interactuado")

        score = customer.lead_score or 0
        if score < 5 and customer.lead_status not in ("won", "lost"):
            risk_score += 15
            factors.append("Lead score muy bajo")
        elif score < 15:
            risk_score += 5

        if customer.lead_status == "lost":
            risk_score += 50
            factors.append("Cliente marcado como perdido")
        elif customer.lead_status == "won":
            risk_score -= 20
            factors.append("Cliente convertido - baja probabilidad de churn")

        conv_count = customer.conversation_count or 0
        if conv_count == 0:
            risk_score += 10
            factors.append("Sin conversaciones registradas")

        if risk_score >= 50:
            risk_level = "high"
        elif risk_score >= 25:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "risk": risk_level,
            "risk_score": risk_score,
            "factors": factors,
            "days_since_last_interaction": self._days_since(customer.last_interaction_at),
            "lead_status": customer.lead_status,
            "lead_score": score,
        }

    async def batch_evaluate_churn(
        self, *, empresa_id: UUID, customer_ids: list[UUID]
    ) -> list[dict]:
        results = []
        for cid in customer_ids:
            evaluation = await self.evaluate_churn(
                empresa_id=empresa_id, customer_id=cid
            )
            evaluation["customer_id"] = str(cid)
            results.append(evaluation)
        return sorted(results, key=lambda r: r.get("risk_score", 0), reverse=True)

    async def get_at_risk_customers(
        self, *, empresa_id: UUID, min_risk: str = "medium"
    ) -> list[dict]:
        result = await self._session.execute(
            select(Cliente).where(
                Cliente.empresa_id == empresa_id,
                Cliente.deleted_at.is_(None),
            )
        )
        customers = list(result.scalars().all())
        at_risk = []
        for c in customers:
            evaluation = await self.evaluate_churn(
                empresa_id=empresa_id, customer_id=c.id
            )
            risk_order = {"low": 0, "medium": 1, "high": 2}
            min_order = {"low": 0, "medium": 1, "high": 2}.get(min_risk, 0)
            if risk_order.get(evaluation["risk"], 0) >= min_order:
                at_risk.append({
                    "customer_id": str(c.id),
                    "full_name": c.full_name,
                    "risk": evaluation["risk"],
                    "risk_score": evaluation["risk_score"],
                    "factors": evaluation["factors"],
                    "days_since_last_interaction": evaluation["days_since_last_interaction"],
                    "lead_score": evaluation["lead_score"],
                })
        return at_risk

    async def _get_customer(self, empresa_id: UUID, customer_id: UUID) -> Cliente | None:
        result = await self._session.execute(
            select(Cliente).where(
                Cliente.empresa_id == empresa_id,
                Cliente.id == customer_id,
                Cliente.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    def _days_since(self, dt: datetime | None) -> int | None:
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return (datetime.now(UTC) - dt).days
