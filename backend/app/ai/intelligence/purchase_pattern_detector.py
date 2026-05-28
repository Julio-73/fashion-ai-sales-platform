import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.conversations.models import ConversationCore, MessageCore
from app.modules.customers.models import Cliente

logger = logging.getLogger("ai_sales_agent.ai.intelligence.purchase_pattern")


class PurchasePatternDetector:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def detect_patterns(
        self, *, empresa_id: UUID, customer_id: UUID
    ) -> dict:
        messages = await self._get_messages(empresa_id, customer_id)
        all_text = " ".join(m.content.lower() for m in messages) if messages else ""

        patterns = {
            "prefiere_negro": "negro" in all_text or "black" in all_text,
            "prefiere_oversize": "oversize" in all_text or "holgado" in all_text,
            "busca_premium": any(kw in all_text for kw in ["premium", "calidad", "lujo", "exclusivo"]),
            "busca_ofertas": any(kw in all_text for kw in ["descuento", "oferta", "barato", "rebaja"]),
            "compra_frecuente": any(kw in all_text for kw in ["siempre compro", "habitual", "soy cliente"]),
            "prefiere_streetwear": any(kw in all_text for kw in ["streetwear", "urbano", "callejero"]),
            "busca_elegante": any(kw in all_text for kw in ["elegante", "formal", "vestir", "fiesta"]),
            "prefiere_deportivo": any(kw in all_text for kw in ["deportivo", "sport", "cómodo"]),
        }

        return {
            "detected_patterns": {k: v for k, v in patterns.items() if v},
            "total_patterns": sum(1 for v in patterns.values() if v),
            "message_count": len(messages),
        }

    async def detect_frequent_combinations(
        self, *, empresa_id: UUID, customer_id: UUID
    ) -> list[dict]:
        raw = text("""
            SELECT mc.content, mc.created_at
            FROM messages_core mc
            JOIN conversations_core cc ON cc.id = mc.conversation_id
            WHERE cc.empresa_id = :eid
              AND cc.customer_id = :cid
            ORDER BY mc.created_at ASC
        """)
        result = await self._session.execute(
            raw, {"eid": empresa_id, "cid": customer_id}
        )
        contents = [row.content for row in result if row.content]

        combos = []
        for i in range(len(contents) - 1):
            combined = (contents[i] + " " + contents[i + 1]).lower()
            if any(kw in combined for kw in ["vestido", "zapatos", "falda", "pantalón", "camisa"]):
                combos.append({
                    "messages": [contents[i][:100], contents[i + 1][:100]],
                    "detected": True,
                })
        return combos[:10]

    async def detect_seasonal_preferences(
        self, *, empresa_id: UUID, customer_id: UUID
    ) -> dict:
        messages = await self._get_messages(empresa_id, customer_id)
        all_text = " ".join(m.content.lower() for m in messages) if messages else ""

        season_keywords = {
            "verano": ["verano", "calor", "playa", "short", "camiseta"],
            "invierno": ["invierno", "frío", "abrigo", "chaqueta", "bufanda"],
            "primavera": ["primavera", "floral", "ligero"],
            "otoño": ["otoño", "capa", "suéter"],
        }

        detected = {}
        for season, kws in season_keywords.items():
            matches = [kw for kw in kws if kw in all_text]
            if matches:
                detected[season] = matches

        return {
            "detected_seasons": detected,
            "primary_season": max(detected, key=lambda s: len(detected[s])) if detected else None,
        }

    async def _get_messages(
        self, empresa_id: UUID, customer_id: UUID
    ) -> list[MessageCore]:
        result = await self._session.execute(
            select(MessageCore)
            .join(ConversationCore, MessageCore.conversation_id == ConversationCore.id)
            .where(
                ConversationCore.empresa_id == empresa_id,
                ConversationCore.customer_id == customer_id,
            )
            .order_by(MessageCore.created_at.desc())
            .limit(200)
        )
        return list(result.scalars().all())
