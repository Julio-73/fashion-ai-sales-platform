"""Sales Intelligence Service — orchestrates intent classification, scoring, and rules.

Flow:
  1. Classify message intent(s)
  2. Calculate lead score
  3. Evaluate sales rules
  4. Return structured result for CRM integration
"""

from __future__ import annotations

from app.sales.classifiers.intent_classifier import IntentClassifier
from app.sales.rules.sales_rules import RuleContext, SalesRulesEngine
from app.sales.schemas.sales_schemas import SalesIntelligenceInput, SalesIntelligenceResult
from app.sales.scoring.lead_scorer import LeadScorer


class SalesIntelligenceService:
    def __init__(
        self,
        classifier: IntentClassifier | None = None,
        scorer: LeadScorer | None = None,
        rules_engine: SalesRulesEngine | None = None,
    ) -> None:
        self._classifier = classifier or IntentClassifier()
        self._scorer = scorer or LeadScorer()
        self._rules_engine = rules_engine or SalesRulesEngine()

    async def analyze(self, input_data: SalesIntelligenceInput) -> SalesIntelligenceResult:
        all_intents = self._classifier.classify_all(input_data.message_content)
        primary_intent, _ = self._classifier.classify(input_data.message_content)
        intent_labels = [i.value for i, _ in all_intents]

        score = self._scorer.calculate_score(
            intent_labels=intent_labels,
            message_count=input_data.message_count,
            conversation_count=input_data.conversation_count,
            last_interaction_at=input_data.last_interaction_at,
        )
        priority = self._scorer.score_to_priority(score)

        rule_context = RuleContext(
            empresa_id=input_data.empresa_id,
            customer_id=input_data.customer_id,
            current_lead_status=input_data.current_lead_status,
            current_priority=priority,
            current_score=score,
            conversation_count=input_data.conversation_count,
            last_intents=intent_labels,
            existing_tags=(),
        )
        rule_results = self._rules_engine.evaluate_all(rule_context)

        suggested_tags: list[str] = []
        suggested_lead_status: str | None = None
        reason: str | None = None
        for rr in rule_results:
            if rr.suggested_tags:
                suggested_tags.extend(rr.suggested_tags)
            if rr.suggested_lead_status and suggested_lead_status is None:
                suggested_lead_status = rr.suggested_lead_status
                reason = rr.reason

        return SalesIntelligenceResult(
            primary_intent=primary_intent,
            all_intents=all_intents,
            lead_score=score,
            lead_priority=priority,
            suggested_lead_status=suggested_lead_status,
            suggested_tags=suggested_tags,
            reason=reason,
        )
