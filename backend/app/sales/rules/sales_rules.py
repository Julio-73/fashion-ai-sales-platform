"""Sales rules engine — applies business rules to determine lead lifecycle transitions.

Rules are desacopladas, extensibles, and evaluated in order.
Each rule can suggest a new lead_status or priority adjustment.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from uuid import UUID


@dataclass
class RuleEvaluationResult:
    suggested_lead_status: str | None = None
    suggested_priority: str | None = None
    suggested_tags: list[str] = field(default_factory=list)
    reason: str | None = None


@dataclass
class RuleContext:
    empresa_id: UUID
    customer_id: UUID
    current_lead_status: str
    current_priority: str
    current_score: int
    conversation_count: int
    last_intents: list[str]
    existing_tags: tuple[str, ...]


class SalesRule(ABC):
    @abstractmethod
    def evaluate(self, context: RuleContext) -> RuleEvaluationResult | None:
        ...


class FrequentBuyerRule(SalesRule):
    def evaluate(self, context: RuleContext) -> RuleEvaluationResult | None:
        if context.conversation_count >= 5 and context.current_lead_status == "new":
            return RuleEvaluationResult(
                suggested_lead_status="interested",
                suggested_tags=["frequent"],
                reason="high conversation frequency",
            )
        return None


class HighScorePromotionRule(SalesRule):
    def evaluate(self, context: RuleContext) -> RuleEvaluationResult | None:
        if context.current_score >= 60 and context.current_lead_status != "negotiating":
            return RuleEvaluationResult(
                suggested_lead_status="hot",
                reason=f"score {context.current_score} exceeds hot threshold",
            )
        return None


class InterestToNegotiationRule(SalesRule):
    def evaluate(self, context: RuleContext) -> RuleEvaluationResult | None:
        if (
            context.current_score >= 30
            and context.current_lead_status == "interested"
        ):
            return RuleEvaluationResult(
                suggested_lead_status="negotiating",
                reason=f"score {context.current_score} indicates negotiation readiness",
            )
        return None


_DEFAULT_RULES: list[SalesRule] = [
    FrequentBuyerRule(),
    HighScorePromotionRule(),
    InterestToNegotiationRule(),
]


class SalesRulesEngine:
    def __init__(self, rules: list[SalesRule] | None = None) -> None:
        self._rules = rules or _DEFAULT_RULES

    def evaluate_all(self, context: RuleContext) -> list[RuleEvaluationResult]:
        results: list[RuleEvaluationResult] = []
        for rule in self._rules:
            result = rule.evaluate(context)
            if result is not None:
                results.append(result)
        return results
