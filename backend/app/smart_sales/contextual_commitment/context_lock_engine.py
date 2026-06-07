import logging
from dataclasses import dataclass, field

from app.smart_sales.contextual_commitment.selected_product_tracker import (
    SelectedProductTracker,
)
from app.smart_sales.contextual_commitment.commitment_state_machine import (
    CommitmentStage,
    CommitmentStateMachine,
)

logger = logging.getLogger("ai_sales_agent.smart_sales.contextual_commitment.lock")


@dataclass
class LockResult:
    is_locked: bool = False
    locked_product: str | None = None
    locked_color: str | None = None
    locked_size: str | None = None
    locked_category: str | None = None
    commitment_stage: CommitmentStage = CommitmentStage.BROWSING
    recovery_data: dict = field(default_factory=dict)

    def should_bypass_catalog(self) -> bool:
        return self.is_locked

    def should_prevent_catalog_listing(self) -> bool:
        return self.is_locked


class ContextLockEngine:
    def __init__(
        self,
        tracker: SelectedProductTracker,
        state_machine: CommitmentStateMachine,
    ) -> None:
        self._tracker = tracker
        self._state_machine = state_machine

    def evaluate(
        self,
        conversation_id: str,
        user_message: str,
    ) -> LockResult:
        data = self._tracker.detect(conversation_id, user_message)
        current_stage = self._state_machine.get_stage(conversation_id)
        result = LockResult(
            commitment_stage=current_stage,
        )

        is_rejection = data.commitment_level.value <= 1 and data.has_any_selection()
        if is_rejection and current_stage in {
            CommitmentStage.PRODUCT_SELECTED,
            CommitmentStage.SIZE_SELECTED,
            CommitmentStage.READY_TO_BUY,
        }:
            self._state_machine.transition(conversation_id, CommitmentStage.BROWSING)
            if data.last_rejection_category:
                result.recovery_data["category"] = data.last_rejection_category
            if data.rejected_products:
                result.recovery_data["rejected"] = list(data.rejected_products)
            return result

        if data.is_committed() and not is_rejection:
            result.is_locked = True
            result.locked_product = data.selected_product
            result.locked_color = data.selected_color
            result.locked_size = data.selected_size
            result.locked_category = data.selected_category

            if data.is_confirmed():
                target = (
                    CommitmentStage.SIZE_SELECTED
                    if data.selected_size
                    else CommitmentStage.CHECKOUT_READY
                    if data.confirmation_count >= 2
                    else CommitmentStage.READY_TO_BUY
                )
            else:
                target = CommitmentStage.PRODUCT_SELECTED

            self._state_machine.transition(conversation_id, target)
            result.commitment_stage = self._state_machine.get_stage(conversation_id)

        return result

    def lock_product(
        self,
        conversation_id: str,
        *,
        product_name: str,
        product_id: str | None = None,
        category: str | None = None,
    ) -> None:
        self._tracker.set_selected_product(
            conversation_id=conversation_id,
            product_name=product_name,
            product_id=product_id,
            category=category,
        )
        self._state_machine.transition(conversation_id, CommitmentStage.PRODUCT_SELECTED)

    def is_locked(self, conversation_id: str) -> bool:
        return self._state_machine.is_locked(conversation_id)

    def release(self, conversation_id: str) -> None:
        self._state_machine.reset(conversation_id)

    def clear(self, conversation_id: str) -> None:
        self._tracker.clear(conversation_id)
        self._state_machine.clear(conversation_id)

    def get_stage(self, conversation_id: str) -> CommitmentStage:
        return self._state_machine.get_stage(conversation_id)
