import logging
from enum import Enum

logger = logging.getLogger("ai_sales_agent.smart_sales.contextual_commitment.state_machine")


class CommitmentStage(Enum):
    BROWSING = "browsing"
    INTERESTED = "interested"
    PRODUCT_SELECTED = "product_selected"
    SIZE_SELECTED = "size_selected"
    READY_TO_BUY = "ready_to_buy"
    CHECKOUT_READY = "checkout_ready"


TRANSITIONS: dict[CommitmentStage, set[CommitmentStage]] = {
    CommitmentStage.BROWSING: {CommitmentStage.INTERESTED, CommitmentStage.PRODUCT_SELECTED},
    CommitmentStage.INTERESTED: {CommitmentStage.PRODUCT_SELECTED, CommitmentStage.BROWSING},
    CommitmentStage.PRODUCT_SELECTED: {
        CommitmentStage.SIZE_SELECTED,
        CommitmentStage.READY_TO_BUY,
        CommitmentStage.BROWSING,
    },
    CommitmentStage.SIZE_SELECTED: {
        CommitmentStage.READY_TO_BUY,
        CommitmentStage.PRODUCT_SELECTED,
        CommitmentStage.BROWSING,
    },
    CommitmentStage.READY_TO_BUY: {
        CommitmentStage.CHECKOUT_READY,
        CommitmentStage.PRODUCT_SELECTED,
        CommitmentStage.BROWSING,
    },
    CommitmentStage.CHECKOUT_READY: {
        CommitmentStage.READY_TO_BUY,
        CommitmentStage.BROWSING,
    },
}


REJECTION_TRIGGERS: set[CommitmentStage] = {
    CommitmentStage.PRODUCT_SELECTED,
    CommitmentStage.SIZE_SELECTED,
    CommitmentStage.READY_TO_BUY,
    CommitmentStage.CHECKOUT_READY,
}


class CommitmentStateMachine:
    def __init__(self) -> None:
        self._stages: dict[str, CommitmentStage] = {}

    def get_stage(self, conversation_id: str) -> CommitmentStage:
        return self._stages.get(conversation_id, CommitmentStage.BROWSING)

    def transition(
        self,
        conversation_id: str,
        target: CommitmentStage,
    ) -> CommitmentStage:
        current = self.get_stage(conversation_id)
        if target == current:
            return current
        allowed = TRANSITIONS.get(current, set())
        if target not in allowed:
            logger.debug(
                "Blocked transition %s -> %s for %s",
                current.value, target.value, conversation_id,
            )
            return current
        logger.info(
            "State transition %s -> %s for %s",
            current.value, target.value, conversation_id,
        )
        self._stages[conversation_id] = target
        return target

    def is_locked(self, conversation_id: str) -> bool:
        stage = self.get_stage(conversation_id)
        return stage in {
            CommitmentStage.PRODUCT_SELECTED,
            CommitmentStage.SIZE_SELECTED,
            CommitmentStage.READY_TO_BUY,
            CommitmentStage.CHECKOUT_READY,
        }

    def reset(self, conversation_id: str) -> None:
        self._stages.pop(conversation_id, None)

    def clear(self, conversation_id: str) -> None:
        self.reset(conversation_id)
