"""AutomationAIService — deterministic commercial advisor.

Generates:

* ``priority``            — one of low / medium / high / critical
* ``reason``              — short Spanish explanation
* ``next_best_action``    — one canonical action verb
* ``score``               — 0-100 urgency score

We deliberately do NOT call any LLM — this is the same pattern used
by ``app.modules.pipeline.ai.CommercialAI``. All signals come from
data we already read from frozen modules.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from app.modules.automation.models import (
    RULE_001,
    RULE_002,
    RULE_003,
    RULE_004,
    RULE_005,
    RULE_006,
    RULE_007,
)
from app.modules.customers.models import Cliente
from app.modules.pipeline.models import (
    LOST_STAGE,
    WON_STAGE,
    SalesPipelineItem,
)


# ---------------------------------------------------------------------------
# Action catalog — must be small and stable for the UI
# ---------------------------------------------------------------------------
ACTION_CALL = "Llamar hoy."
ACTION_PROPOSAL = "Enviar propuesta."
ACTION_MEETING = "Agendar reunión."
ACTION_DISCOUNT = "Enviar descuento."
ACTION_ESCALATE = "Escalar a ejecutivo."
ACTION_FOLLOW_UP = "Hacer follow-up por WhatsApp."
ACTION_RECOVERY = "Campaña de recuperación."
ACTION_WIN_LOG = "Registrar motivo de cierre ganado."
ACTION_LOSS_LOG = "Registrar motivo de cierre perdido."
ACTION_MONITOR = "Mantener en nurturing."


_NEXT_ACTION_BY_RULE: dict[str, str] = {
    RULE_001: ACTION_FOLLOW_UP,
    RULE_002: ACTION_CALL,
    RULE_003: ACTION_PROPOSAL,
    RULE_004: ACTION_RECOVERY,
    RULE_005: ACTION_ESCALATE,
    RULE_006: ACTION_WIN_LOG,
    RULE_007: ACTION_LOSS_LOG,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _clamp(value: int, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, value))


def _days_since(when: datetime | None, now: datetime) -> int:
    if when is None:
        return 0
    delta = now - when
    if delta.total_seconds() <= 0:
        return 0
    return int(delta.total_seconds() // 86_400)


def _hours_since(when: datetime | None, now: datetime) -> int:
    if when is None:
        return 0
    delta = now - when
    if delta.total_seconds() <= 0:
        return 0
    return int(delta.total_seconds() // 3600)


@dataclass
class _Signals:
    """Snapshot used to derive the recommendation. No I/O."""

    rule_key: str
    customer_idle_hours: int = 0
    customer_idle_days: int = 0
    stage_entered_days: int = 0
    deal_value: Decimal = Decimal("0")
    lifetime_value: Decimal = Decimal("0")
    is_vip: bool = False
    is_high_value: bool = False
    is_won: bool = False
    is_lost: bool = False
    lead_score: int = 0
    last_message_hours: int | None = None


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------
class AutomationAIService:
    """Pure (no I/O) — easy to unit-test."""

    HIGH_VALUE_THRESHOLD = Decimal("2000")

    def _signals_for(
        self,
        rule_key: str,
        customer: Cliente | None,
        deal: SalesPipelineItem | None,
        ltv: Decimal,
        last_message_at: datetime | None,
        now: datetime,
    ) -> _Signals:
        s = _Signals(rule_key=rule_key)
        if customer is not None:
            s.customer_idle_hours = _hours_since(customer.last_interaction_at, now)
            s.customer_idle_days = _days_since(customer.last_interaction_at, now)
            s.lead_score = int(customer.lead_score or 0)
        if deal is not None:
            s.deal_value = deal.estimated_value or Decimal("0")
            s.stage_entered_days = _days_since(deal.stage_entered_at, now)
            s.is_vip = bool(deal.is_vip)
            s.is_high_value = (
                s.deal_value >= self.HIGH_VALUE_THRESHOLD
                or ltv >= self.HIGH_VALUE_THRESHOLD
            )
            s.is_won = deal.stage == WON_STAGE
            s.is_lost = deal.stage == LOST_STAGE
        s.lifetime_value = ltv
        if last_message_at is not None:
            s.last_message_hours = _hours_since(last_message_at, now)
        return s

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def recommend(
        self,
        rule_key: str,
        *,
        customer: Cliente | None,
        deal: SalesPipelineItem | None,
        lifetime_value: Decimal = Decimal("0"),
        last_message_at: datetime | None = None,
        now: datetime | None = None,
    ) -> tuple[str, str, str, int]:
        """Return ``(priority, reason, next_best_action, score)``."""
        if now is None:
            now = datetime.now(timezone.utc)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        s = self._signals_for(
            rule_key, customer, deal, lifetime_value, last_message_at, now
        )
        priority = self._priority(rule_key, s)
        score = self._score(rule_key, s)
        reason = self._reason(rule_key, s, priority)
        next_action = self._next_action(rule_key, deal, s)
        return priority, reason, next_action, score

    # ------------------------------------------------------------------
    # Priority
    # ------------------------------------------------------------------
    def _priority(self, rule_key: str, s: _Signals) -> str:
        if rule_key == RULE_002 and s.customer_idle_hours >= 48:
            return "critical"
        if rule_key == RULE_004:
            return "critical" if s.is_vip else "high"
        if rule_key == RULE_005 and s.is_high_value:
            return "high"
        if rule_key == RULE_003 and s.stage_entered_days >= 14:
            return "critical"
        if rule_key == RULE_001 and s.customer_idle_hours >= 36:
            return "high"
        if rule_key == RULE_006:
            return "low"
        if rule_key == RULE_007:
            return "medium"
        return "medium"

    # ------------------------------------------------------------------
    # Score 0-100
    # ------------------------------------------------------------------
    def _score(self, rule_key: str, s: _Signals) -> int:
        if rule_key == RULE_001:
            base = 30 + min(s.customer_idle_hours, 96) // 2
            return _clamp(base + (10 if s.lead_score >= 50 else 0))
        if rule_key == RULE_002:
            base = 60 + min(max(s.customer_idle_hours - 48, 0), 96) // 2
            return _clamp(base + (15 if s.lead_score >= 70 else 0))
        if rule_key == RULE_003:
            base = 50 + min(s.stage_entered_days, 30) * 2
            return _clamp(base + (10 if s.is_vip else 0))
        if rule_key == RULE_004:
            base = 70 + min(s.customer_idle_days, 60)
            return _clamp(base + (15 if s.is_vip else 0))
        if rule_key == RULE_005:
            base = 50
            if s.is_high_value:
                base += 30
            if s.is_vip:
                base += 10
            return _clamp(base + min(int(s.lead_score / 4), 10))
        if rule_key == RULE_006:
            return 40
        if rule_key == RULE_007:
            return 50
        return 40

    # ------------------------------------------------------------------
    # Reason
    # ------------------------------------------------------------------
    def _reason(self, rule_key: str, s: _Signals, priority: str) -> str:
        if rule_key == RULE_001:
            return (
                f"Lead sin respuesta hace {s.customer_idle_hours} h. "
                "Recomendado: outreach de reactivación."
            )
        if rule_key == RULE_002:
            return (
                f"Lead en silencio {s.customer_idle_hours} h — riesgo de "
                "fuga elevado. Priorizar contacto humano."
            )
        if rule_key == RULE_003:
            return (
                f"Deal lleva {s.stage_entered_days} días en 'negotiation'. "
                "Revisar objeciones y/o cerrar con descuento."
            )
        if rule_key == RULE_004:
            tag = "VIP" if s.is_vip else "de alto valor"
            return (
                f"Cliente {tag} sin interacción hace {s.customer_idle_days} "
                "días. Iniciar campaña de recuperación."
            )
        if rule_key == RULE_005:
            parts = ["Nuevo lead detectado"]
            if s.is_high_value:
                parts.append("alto valor")
            if s.is_vip:
                parts.append("VIP")
            if s.lead_score:
                parts.append(f"score {s.lead_score}")
            return ". ".join(parts) + "."
        if rule_key == RULE_006:
            return "Deal ganado — registrar motivo y arrancar onboarding."
        if rule_key == RULE_007:
            return (
                f"Deal perdido tras {s.stage_entered_days} días en "
                "negociación. Registrar motivo en CRM."
            )
        return f"Regla {rule_key} activada."

    # ------------------------------------------------------------------
    # Next action
    # ------------------------------------------------------------------
    def _next_action(
        self, rule_key: str, deal: SalesPipelineItem | None, s: _Signals
    ) -> str:
        if rule_key == RULE_003 and s.stage_entered_days >= 14:
            return ACTION_ESCALATE
        if rule_key == RULE_005 and s.is_high_value:
            return ACTION_ESCALATE
        return _NEXT_ACTION_BY_RULE.get(rule_key, ACTION_MONITOR)


__all__ = [
    "AutomationAIService",
    "ACTION_CALL",
    "ACTION_PROPOSAL",
    "ACTION_MEETING",
    "ACTION_DISCOUNT",
    "ACTION_ESCALATE",
    "ACTION_FOLLOW_UP",
    "ACTION_RECOVERY",
    "ACTION_WIN_LOG",
    "ACTION_LOSS_LOG",
    "ACTION_MONITOR",
]
