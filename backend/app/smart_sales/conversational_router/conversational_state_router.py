from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict

from .conversational_intent_detector import ConversationalIntent


class ConversationStage(str, Enum):
    greeting = "greeting"
    browsing = "browsing"
    exploring = "exploring"
    styling = "styling"
    considering = "considering"
    committed = "committed"
    checkout_ready = "checkout_ready"
    closing = "closing"
    post_purchase = "post_purchase"


STAGE_ORDER: list[ConversationStage] = [
    ConversationStage.greeting,
    ConversationStage.browsing,
    ConversationStage.exploring,
    ConversationStage.styling,
    ConversationStage.considering,
    ConversationStage.committed,
    ConversationStage.checkout_ready,
    ConversationStage.closing,
    ConversationStage.post_purchase,
]

ALLOWED_REGRESSIONS: set[tuple[ConversationStage, ConversationStage]] = {
    (ConversationStage.browsing, ConversationStage.greeting),
    (ConversationStage.exploring, ConversationStage.browsing),
    (ConversationStage.considering, ConversationStage.exploring),
    (ConversationStage.styling, ConversationStage.browsing),
}

INTENT_TO_STAGE: dict[ConversationalIntent, ConversationStage] = {
    ConversationalIntent.greeting: ConversationStage.greeting,
    ConversationalIntent.gratitude: ConversationStage.closing,
    ConversationalIntent.casual_chat: ConversationStage.post_purchase,
    ConversationalIntent.hesitation: ConversationStage.considering,
    ConversationalIntent.confusion: ConversationStage.exploring,
    ConversationalIntent.browsing: ConversationStage.browsing,
    ConversationalIntent.interested: ConversationStage.exploring,
    ConversationalIntent.committed: ConversationStage.committed,
    ConversationalIntent.ready_to_buy: ConversationStage.checkout_ready,
    ConversationalIntent.objection: ConversationStage.considering,
    ConversationalIntent.sizing: ConversationStage.styling,
    ConversationalIntent.styling: ConversationStage.styling,
    ConversationalIntent.comparison: ConversationStage.exploring,
    ConversationalIntent.unknown: ConversationStage.browsing,
}


_conversation_stages: dict[str, ConversationStage] = defaultdict(lambda: ConversationStage.greeting)


@dataclass
class StateTransitionResult:
    current_stage: ConversationStage
    previous_stage: ConversationStage
    did_transition: bool
    skipped_stages: list[ConversationStage] = field(default_factory=list)


class ConversationalStateRouter:
    def get_stage(self, conversation_id: str) -> ConversationStage:
        return _conversation_stages.get(conversation_id, ConversationStage.greeting)

    def transition(self, conversation_id: str, intent: ConversationalIntent) -> StateTransitionResult:
        current = self.get_stage(conversation_id)
        target = INTENT_TO_STAGE.get(intent, ConversationStage.browsing)

        if current == target:
            return StateTransitionResult(
                current_stage=current,
                previous_stage=current,
                did_transition=False,
            )

        current_idx = STAGE_ORDER.index(current) if current in STAGE_ORDER else -1
        target_idx = STAGE_ORDER.index(target) if target in STAGE_ORDER else -1

        forward = target_idx > current_idx
        regression_allowed = (current, target) in ALLOWED_REGRESSIONS

        if not forward and not regression_allowed:
            return StateTransitionResult(
                current_stage=current,
                previous_stage=current,
                did_transition=False,
            )

        skipped = []
        if forward and target_idx - current_idx > 1:
            for i in range(current_idx + 1, target_idx):
                skipped.append(STAGE_ORDER[i])

        _conversation_stages[conversation_id] = target

        return StateTransitionResult(
            current_stage=target,
            previous_stage=current,
            did_transition=True,
            skipped_stages=skipped,
        )

    def reset(self, conversation_id: str) -> None:
        _conversation_stages.pop(conversation_id, None)
