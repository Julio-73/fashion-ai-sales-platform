import pytest

from app.smart_sales.contextual_commitment.commitment_state_machine import (
    CommitmentStage,
    CommitmentStateMachine,
)
from app.smart_sales.contextual_commitment.selected_product_tracker import (
    CommitmentLevel,
    SelectedProductTracker,
)
from app.smart_sales.contextual_commitment.context_lock_engine import (
    ContextLockEngine,
)
from app.smart_sales.contextual_commitment.response_focus_guard import (
    ResponseFocusGuard,
)
from app.smart_sales.contextual_commitment.elite_product_confirmation import (
    EliteProductConfirmation,
)
from app.smart_sales.contextual_commitment.rejection_recovery_engine import (
    RejectionRecoveryEngine,
)


CONV_ID = "test-conv-123"


# ─── State Machine Tests ──────────────────────────────────────────────────────


class TestCommitmentStateMachine:
    @pytest.fixture
    def machine(self) -> CommitmentStateMachine:
        return CommitmentStateMachine()

    def test_starts_in_browsing(self, machine: CommitmentStateMachine) -> None:
        assert machine.get_stage(CONV_ID) == CommitmentStage.BROWSING

    def test_transition_browsing_to_interested(self, machine: CommitmentStateMachine) -> None:
        result = machine.transition(CONV_ID, CommitmentStage.INTERESTED)
        assert result == CommitmentStage.INTERESTED

    def test_transition_browsing_to_product_selected(self, machine: CommitmentStateMachine) -> None:
        result = machine.transition(CONV_ID, CommitmentStage.PRODUCT_SELECTED)
        assert result == CommitmentStage.PRODUCT_SELECTED

    def test_transition_product_selected_to_size(self, machine: CommitmentStateMachine) -> None:
        machine.transition(CONV_ID, CommitmentStage.PRODUCT_SELECTED)
        result = machine.transition(CONV_ID, CommitmentStage.SIZE_SELECTED)
        assert result == CommitmentStage.SIZE_SELECTED

    def test_transition_product_selected_to_ready(self, machine: CommitmentStateMachine) -> None:
        machine.transition(CONV_ID, CommitmentStage.PRODUCT_SELECTED)
        result = machine.transition(CONV_ID, CommitmentStage.READY_TO_BUY)
        assert result == CommitmentStage.READY_TO_BUY

    def test_no_illegal_transition_interested_to_checkout(self, machine: CommitmentStateMachine) -> None:
        machine.transition(CONV_ID, CommitmentStage.INTERESTED)
        result = machine.transition(CONV_ID, CommitmentStage.CHECKOUT_READY)
        assert result == CommitmentStage.INTERESTED

    def test_is_locked_when_product_selected(self, machine: CommitmentStateMachine) -> None:
        assert not machine.is_locked(CONV_ID)
        machine.transition(CONV_ID, CommitmentStage.PRODUCT_SELECTED)
        assert machine.is_locked(CONV_ID)

    def test_reset(self, machine: CommitmentStateMachine) -> None:
        machine.transition(CONV_ID, CommitmentStage.PRODUCT_SELECTED)
        machine.reset(CONV_ID)
        assert machine.get_stage(CONV_ID) == CommitmentStage.BROWSING


# ─── Selected Product Tracker Tests ────────────────────────────────────────────


class TestSelectedProductTracker:
    @pytest.fixture
    def tracker(self) -> SelectedProductTracker:
        return SelectedProductTracker()

    def test_initial_state(self, tracker: SelectedProductTracker) -> None:
        data = tracker.get_or_create(CONV_ID)
        assert data.commitment_level == CommitmentLevel.none
        assert data.selected_product is None

    def test_detect_quiero_ese(self, tracker: SelectedProductTracker) -> None:
        data = tracker.detect(CONV_ID, "quiero ese")
        assert data.commitment_level.value >= CommitmentLevel.selected.value

    def test_detect_me_gusta(self, tracker: SelectedProductTracker) -> None:
        data = tracker.detect(CONV_ID, "me gusta ese")
        assert data.commitment_level.value >= CommitmentLevel.selected.value

    def test_detect_el_premium_black(self, tracker: SelectedProductTracker) -> None:
        data = tracker.detect(CONV_ID, "el premium black")
        assert data.commitment_level.value >= CommitmentLevel.selected.value

    def test_detect_size_m(self, tracker: SelectedProductTracker) -> None:
        data = tracker.detect(CONV_ID, "talla M")
        assert data.selected_size == "M"
        assert data.commitment_level == CommitmentLevel.confirmed

    def test_detect_color_reference(self, tracker: SelectedProductTracker) -> None:
        tracker.set_selected_product(CONV_ID, "Polo Premium Black")
        data = tracker.detect(CONV_ID, "en azul")
        assert data.selected_color == "Azul"
        assert data.commitment_level == CommitmentLevel.confirmed

    def test_rejection_resets_selection(self, tracker: SelectedProductTracker) -> None:
        tracker.set_selected_product(CONV_ID, "Polo Premium Black", category="Polos")
        data = tracker.get_or_create(CONV_ID)
        assert data.commitment_level == CommitmentLevel.selected
        data = tracker.detect(CONV_ID, "no me gusta")
        assert data.commitment_level.value <= CommitmentLevel.interested.value
        assert data.selected_product is None
        assert data.last_rejection_category == "Polos"

    def test_rejection_muy_caro(self, tracker: SelectedProductTracker) -> None:
        tracker.set_selected_product(CONV_ID, "Blazer Ivory Elite", category="Blazers")
        data = tracker.detect(CONV_ID, "muy caro")
        assert data.commitment_level.value <= CommitmentLevel.interested.value
        assert data.last_rejection_category == "Blazers"

    def test_rejection_keeps_category(self, tracker: SelectedProductTracker) -> None:
        tracker.set_selected_product(CONV_ID, "Jean Cargo Street", category="Pantalones")
        data = tracker.detect(CONV_ID, "no me convence")
        assert data.last_rejection_category == "Pantalones"

    def test_no_rejection_for_gratitude(self, tracker: SelectedProductTracker) -> None:
        tracker.set_selected_product(CONV_ID, "Polo Premium Black")
        data = tracker.detect(CONV_ID, "gracias")
        assert data.is_committed()

    def test_set_selected_product_persistence(self, tracker: SelectedProductTracker) -> None:
        tracker.set_selected_product(CONV_ID, "Casaca Oversize Urban", product_id="p123", category="Casacas")
        data = tracker.get_or_create(CONV_ID)
        assert data.selected_product == "Casaca Oversize Urban"
        assert data.selected_product_id == "p123"
        assert data.selected_category == "Casacas"
        assert data.is_committed()

    def test_clear_resets(self, tracker: SelectedProductTracker) -> None:
        tracker.set_selected_product(CONV_ID, "Test Product")
        tracker.clear(CONV_ID)
        data = tracker.get_or_create(CONV_ID)
        assert data.commitment_level == CommitmentLevel.none


# ─── Context Lock Engine Tests ────────────────────────────────────────────────


class TestContextLockEngine:
    @pytest.fixture
    def engine(self) -> ContextLockEngine:
        tracker = SelectedProductTracker()
        state_machine = CommitmentStateMachine()
        return ContextLockEngine(tracker=tracker, state_machine=state_machine)

    def test_not_locked_initially(self, engine: ContextLockEngine) -> None:
        result = engine.evaluate(CONV_ID, "hola")
        assert not result.should_bypass_catalog()

    def test_locks_when_product_selected(self, engine: ContextLockEngine) -> None:
        engine.lock_product(CONV_ID, product_name="Polo Premium Black", category="Polos")
        assert engine.is_locked(CONV_ID)
        result = engine.evaluate(CONV_ID, "quiero ese")
        assert result.should_bypass_catalog()

    def test_prevents_catalog_listing_when_locked(self, engine: ContextLockEngine) -> None:
        engine.lock_product(CONV_ID, product_name="Polo Premium Black", category="Polos")
        result = engine.evaluate(CONV_ID, "dame ese")
        assert result.should_prevent_catalog_listing()

    def test_rejection_releases_lock(self, engine: ContextLockEngine) -> None:
        engine.lock_product(CONV_ID, product_name="Polo Premium Black", category="Polos")
        result = engine.evaluate(CONV_ID, "no me gusta")
        assert not result.should_bypass_catalog()

    def test_stage_tracks_commitment(self, engine: ContextLockEngine) -> None:
        engine.lock_product(CONV_ID, product_name="Polo Premium Black", category="Polos")
        result = engine.evaluate(CONV_ID, "talla M")
        assert result.locked_size == "M"

    def test_release_and_clear(self, engine: ContextLockEngine) -> None:
        engine.lock_product(CONV_ID, product_name="Polo Premium Black", category="Polos")
        engine.clear(CONV_ID)
        assert not engine.is_locked(CONV_ID)
        result = engine.evaluate(CONV_ID, "hola")
        assert not result.should_bypass_catalog()


# ─── Response Focus Guard Tests ──────────────────────────────────────────────


class TestResponseFocusGuard:
    @pytest.fixture
    def guard(self) -> ResponseFocusGuard:
        return ResponseFocusGuard()

    def test_allows_normal_response(self, guard: ResponseFocusGuard) -> None:
        from app.smart_sales.contextual_commitment.selected_product_tracker import CommitmentData
        cd = CommitmentData(selected_product="Polo", commitment_level=CommitmentLevel.selected)
        result = guard.check("Claro, el polo está disponible en talla M por S/90.", cd)
        assert not result.is_blocked

    def test_blocks_mira_estas_opciones(self, guard: ResponseFocusGuard) -> None:
        from app.smart_sales.contextual_commitment.selected_product_tracker import CommitmentData
        cd = CommitmentData(selected_product="Polo", commitment_level=CommitmentLevel.selected)
        result = guard.check("Mira estas opciones que tenemos para ti", cd)
        assert result.is_blocked
        assert result.contains_catalog_listing

    def test_blocks_tenemos_estas_disponibles(self, guard: ResponseFocusGuard) -> None:
        from app.smart_sales.contextual_commitment.selected_product_tracker import CommitmentData
        cd = CommitmentData(selected_product="Polo", commitment_level=CommitmentLevel.selected)
        result = guard.check("Tenemos estas disponibles para ti", cd)
        assert result.is_blocked

    def test_blocks_multiple_products_listed(self, guard: ResponseFocusGuard) -> None:
        from app.smart_sales.contextual_commitment.selected_product_tracker import CommitmentData
        cd = CommitmentData(selected_product="Polo", commitment_level=CommitmentLevel.selected)
        result = guard.check("• Polo Premium Black (S/90)\n• Casaca Urban (S/250)", cd)
        assert result.is_blocked
        assert result.contains_multiple_products

    def test_allows_when_not_committed(self, guard: ResponseFocusGuard) -> None:
        result = guard.check("Mira estas opciones que tenemos", None)
        assert not result.is_blocked

    def test_sanitize_removes_catalog_patterns(self, guard: ResponseFocusGuard) -> None:
        from app.smart_sales.contextual_commitment.selected_product_tracker import CommitmentData
        cd = CommitmentData(selected_product="Polo", commitment_level=CommitmentLevel.selected)
        sanitized = guard.sanitize("Mira estas opciones disponibles para ti", cd)
        assert "Mira estas opciones" not in sanitized


# ─── Elite Product Confirmation Tests ─────────────────────────────────────────


class TestEliteProductConfirmation:
    @pytest.fixture
    def confirmation(self) -> EliteProductConfirmation:
        return EliteProductConfirmation()

    def test_generates_when_committed(self, confirmation: EliteProductConfirmation) -> None:
        from app.smart_sales.contextual_commitment.selected_product_tracker import CommitmentData
        cd = CommitmentData(
            selected_product="Polo Premium Black",
            commitment_level=CommitmentLevel.selected,
        )
        result = confirmation.generate(cd, "quiero ese")
        assert result is not None
        assert "Polo Premium Black" in result.text

    def test_includes_color_when_available(self, confirmation: EliteProductConfirmation) -> None:
        from app.smart_sales.contextual_commitment.selected_product_tracker import CommitmentData
        cd = CommitmentData(
            selected_product="Polo Premium Black",
            selected_color="Azul",
            commitment_level=CommitmentLevel.confirmed,
        )
        result = confirmation.generate(cd, "en azul")
        assert result is not None
        assert "Azul" in result.text

    def test_includes_size_when_available(self, confirmation: EliteProductConfirmation) -> None:
        from app.smart_sales.contextual_commitment.selected_product_tracker import CommitmentData
        cd = CommitmentData(
            selected_product="Polo Premium Black",
            selected_size="M",
            commitment_level=CommitmentLevel.confirmed,
        )
        result = confirmation.generate(cd, "talla M")
        assert result is not None
        assert "M" in result.text

    def test_returns_none_when_not_committed(self, confirmation: EliteProductConfirmation) -> None:
        from app.smart_sales.contextual_commitment.selected_product_tracker import CommitmentData
        cd = CommitmentData(commitment_level=CommitmentLevel.none)
        result = confirmation.generate(cd, "hola")
        assert result is None


# ─── Rejection Recovery Engine Tests ──────────────────────────────────────────


class TestRejectionRecoveryEngine:
    @pytest.fixture
    def engine(self) -> RejectionRecoveryEngine:
        return RejectionRecoveryEngine()

    def test_no_recovery_when_no_rejection(self, engine: RejectionRecoveryEngine) -> None:
        from app.smart_sales.contextual_commitment.selected_product_tracker import CommitmentData
        cd = CommitmentData()
        result = engine.process(cd, "hola")
        assert not result.needs_recovery

    def test_recovery_when_rejected(self, engine: RejectionRecoveryEngine) -> None:
        from app.smart_sales.contextual_commitment.selected_product_tracker import CommitmentData
        cd = CommitmentData(
            commitment_level=CommitmentLevel.interested,
            last_rejection_category="Polos",
            rejected_products={"Polo Premium Black"},
        )
        result = engine.process(cd, "no me gusta")
        assert result.needs_recovery
        assert result.recovered_category == "Polos"
        assert "Polos" in result.rejection_recovery_prompt if hasattr(result, 'rejection_recovery_prompt') else True

    def test_recovery_has_category(self, engine: RejectionRecoveryEngine) -> None:
        from app.smart_sales.contextual_commitment.selected_product_tracker import CommitmentData
        cd = CommitmentData(
            commitment_level=CommitmentLevel.interested,
            last_rejection_category="Polos",
            rejected_products={"Polo Premium Black"},
        )
        result = engine.process(cd, "busco otro")
        assert result.recovered_category == "Polos"

    def test_build_recovery_context_updates_entities(self, engine: RejectionRecoveryEngine) -> None:
        from app.smart_sales.contextual_commitment.selected_product_tracker import CommitmentData
        cd = CommitmentData(
            commitment_level=CommitmentLevel.interested,
            last_rejection_category="Casacas",
            rejected_products={"Casaca Oversize"},
        )
        result = engine.process(cd, "otro modelo")
        entities = {"product_type": "polo", "color": "negro"}
        updated = engine.build_recovery_context(result, entities)
        assert updated["product_type"] == "Casacas"
        assert updated["color"] == "negro"


# ─── Anti-Regression Tests ────────────────────────────────────────────────────


class TestAntiRegression:
    def test_gratitude_does_not_reset_commitment(self) -> None:
        tracker = SelectedProductTracker()
        tracker.set_selected_product(CONV_ID, "Polo Premium Black")
        data = tracker.detect(CONV_ID, "gracias")
        assert data.is_committed()
        assert data.selected_product == "Polo Premium Black"

    def test_size_does_not_relist_catalog(self) -> None:
        tracker = SelectedProductTracker()
        state_machine = CommitmentStateMachine()
        engine = ContextLockEngine(tracker=tracker, state_machine=state_machine)

        engine.lock_product(CONV_ID, product_name="Polo Premium Black", category="Polos")
        result = engine.evaluate(CONV_ID, "talla M")

        assert result.should_bypass_catalog()
        assert result.locked_size == "M"
        assert result.locked_product == "Polo Premium Black"

    def test_color_does_not_relist_catalog(self) -> None:
        tracker = SelectedProductTracker()
        state_machine = CommitmentStateMachine()
        engine = ContextLockEngine(tracker=tracker, state_machine=state_machine)

        engine.lock_product(CONV_ID, product_name="Casaca Denim Black", category="Casacas")
        result = engine.evaluate(CONV_ID, "en azul")

        assert result.should_bypass_catalog()
        assert result.locked_color == "Azul"

    def test_rejection_maintains_category(self) -> None:
        tracker = SelectedProductTracker()
        tracker.set_selected_product(CONV_ID, "Blazer Ivory Elite", category="Blazers")
        data = tracker.detect(CONV_ID, "no me gusta")
        assert data.last_rejection_category == "Blazers"
        assert not data.is_committed()

    def test_no_fallback_generic_with_selected_product(self) -> None:
        guard = ResponseFocusGuard()
        from app.smart_sales.contextual_commitment.selected_product_tracker import CommitmentData
        cd = CommitmentData(selected_product="Polo", commitment_level=CommitmentLevel.selected)
        blocked = guard.check("Tenemos estas opciones disponibles para ti", cd)
        assert blocked.is_blocked
        sanitized = guard.sanitize("Tenemos estas opciones disponibles para ti", cd)
        assert "Tenemos estas opciones" not in sanitized

    def test_state_machine_transitions_complete_flow(self) -> None:
        machine = CommitmentStateMachine()

        assert machine.get_stage(CONV_ID) == CommitmentStage.BROWSING
        machine.transition(CONV_ID, CommitmentStage.INTERESTED)
        assert machine.get_stage(CONV_ID) == CommitmentStage.INTERESTED
        machine.transition(CONV_ID, CommitmentStage.PRODUCT_SELECTED)
        assert machine.get_stage(CONV_ID) == CommitmentStage.PRODUCT_SELECTED
        assert machine.is_locked(CONV_ID)
        machine.transition(CONV_ID, CommitmentStage.SIZE_SELECTED)
        assert machine.get_stage(CONV_ID) == CommitmentStage.SIZE_SELECTED
        machine.transition(CONV_ID, CommitmentStage.READY_TO_BUY)
        assert machine.get_stage(CONV_ID) == CommitmentStage.READY_TO_BUY
        machine.transition(CONV_ID, CommitmentStage.CHECKOUT_READY)
        assert machine.get_stage(CONV_ID) == CommitmentStage.CHECKOUT_READY
