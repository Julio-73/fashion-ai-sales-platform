"""Lead scoring system — calculates customer priority based on commercial signals.

Scores are configurable and extensible. No AI required.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta


@dataclass(frozen=True)
class ScoreSignal:
    condition: str
    points: int


_DEFAULT_SIGNALS: list[ScoreSignal] = [
    ScoreSignal(condition="purchase_intent", points=30),
    ScoreSignal(condition="negotiation_intent", points=15),
    ScoreSignal(condition="product_interest", points=10),
    ScoreSignal(condition="shipping_intent", points=10),
    ScoreSignal(condition="pricing_intent", points=5),
    ScoreSignal(condition="support_intent", points=2),
    ScoreSignal(condition="greeting", points=0),
    ScoreSignal(condition="multiple_messages", points=10),
    ScoreSignal(condition="high_conversation_count", points=15),
    ScoreSignal(condition="recent_activity", points=5),
    ScoreSignal(condition="inactive_7_days", points=-10),
    ScoreSignal(condition="inactive_14_days", points=-20),
    ScoreSignal(condition="inactive_30_days", points=-40),
]


class LeadScorer:
    def __init__(self, signals: list[ScoreSignal] | None = None) -> None:
        self._signals = signals or _DEFAULT_SIGNALS
        self._signal_map = {s.condition: s.points for s in self._signals}

    def calculate_score(
        self,
        *,
        intent_labels: list[str],
        message_count: int,
        conversation_count: int,
        last_interaction_at: datetime | None,
    ) -> int:
        score = 0

        for label in intent_labels:
            score += self._signal_map.get(label, 0)

        if message_count > 1 and "multiple_messages" in self._signal_map:
            score += self._signal_map["multiple_messages"]

        if conversation_count >= 3 and "high_conversation_count" in self._signal_map:
            score += self._signal_map["high_conversation_count"]

        if last_interaction_at:
            now = datetime.now(UTC)
            if last_interaction_at.tzinfo is None:
                last_interaction_at = last_interaction_at.replace(tzinfo=UTC)
            days_since = (now - last_interaction_at).days

            if days_since <= 1 and "recent_activity" in self._signal_map:
                score += self._signal_map["recent_activity"]
            if days_since >= 30 and "inactive_30_days" in self._signal_map:
                score += self._signal_map["inactive_30_days"]
            elif days_since >= 14 and "inactive_14_days" in self._signal_map:
                score += self._signal_map["inactive_14_days"]
            elif days_since >= 7 and "inactive_7_days" in self._signal_map:
                score += self._signal_map["inactive_7_days"]

        return max(0, score)

    @staticmethod
    def score_to_priority(score: int) -> str:
        if score >= 60:
            return "hot"
        if score >= 30:
            return "warm"
        if score >= 10:
            return "cool"
        return "cold"
