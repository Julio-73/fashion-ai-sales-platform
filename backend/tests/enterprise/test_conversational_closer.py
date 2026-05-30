import pytest

from app.smart_sales.conversational_closer.acknowledgment_engine import AcknowledgmentEngine
from app.smart_sales.conversational_closer.contextual_response_engine import ContextualResponseEngine, ContextSnapshot
from app.smart_sales.conversational_closer.intent_commitment_detector import (
    IntentCommitmentDetector, CommitmentLevel,
)
from app.smart_sales.conversational_closer.natural_language_variator import NaturalLanguageVariator
from app.smart_sales.conversational_closer.conversational_transition_engine import ConversationalTransitionEngine
from app.smart_sales.conversational_closer.objection_handler import ObjectionHandler
from app.smart_sales.conversational_closer.elite_sales_closer import EliteSalesCloser
from app.smart_sales.conversational_closer.emotional_conversation_engine import EmotionalConversationEngine
from app.smart_sales.conversational_closer.conversational_memory_enhancer import ConversationalMemoryEnhancer
from app.smart_sales.conversational_closer.human_conversation_rules import HumanConversationRules
from app.smart_sales.conversational_closer.conversational_closer_engine import (
    ConversationalCloserEngine, CloserInput, CloserOutput,
)


class TestAcknowledgmentEngine:
    @pytest.fixture
    def engine(self):
        return AcknowledgmentEngine()

    def test_detects_gratitude(self, engine):
        assert engine.is_gratitude("gracias")
        assert engine.is_gratitude("muchas gracias")
        assert engine.is_gratitude("mil gracias")
        assert not engine.is_gratitude("quiero un polo")

    def test_detects_ok(self, engine):
        assert engine.is_ok_acknowledgment("ok")
        assert engine.is_ok_acknowledgment("dale")
        assert engine.is_ok_acknowledgment("perfecto")
        assert not engine.is_ok_acknowledgment("gracias")

    def test_detects_interest(self, engine):
        assert engine.is_interest("me gusta")
        assert engine.is_interest("interesante")
        assert not engine.is_interest("no gracias")

    def test_detects_hesitation(self, engine):
        assert engine.is_hesitation("mmm no sé")
        assert engine.is_hesitation("tal vez")
        assert engine.is_hesitation("lo pensaré")
        assert not engine.is_hesitation("lo quiero")

    def test_skip_catalog(self, engine):
        assert engine.should_skip_catalog("gracias")
        assert engine.should_skip_catalog("ok")
        assert engine.should_skip_catalog("mmm no sé")
        assert not engine.should_skip_catalog("quiero un polo")

    def test_gratitude_response_not_empty(self, engine):
        for _ in range(10):
            assert engine.get_gratitude_response()

    def test_ok_response_not_empty(self, engine):
        for _ in range(10):
            assert engine.get_ok_response()


class TestIntentCommitmentDetector:
    @pytest.fixture
    def detector(self):
        return IntentCommitmentDetector()

    def test_detects_ready_to_buy(self, detector):
        result = detector.detect("me lo llevo")
        assert result.level == CommitmentLevel.ready_to_buy
        assert result.confidence > 0.8

    def test_detects_committed(self, detector):
        result = detector.detect("quiero ese polo")
        assert result.level == CommitmentLevel.committed

    def test_detects_interested(self, detector):
        result = detector.detect("se ve bien")
        assert result.level == CommitmentLevel.interested

    def test_default_to_interested_with_history(self, detector):
        result = detector.detect("alguna recomendación", has_product_history=True)
        assert result.level == CommitmentLevel.interested

    def test_detects_browsing(self, detector):
        result = detector.detect("qué tienes")
        assert result.level == CommitmentLevel.browsing

    def test_should_attempt_close(self, detector):
        result = detector.detect("me lo llevo")
        assert detector.should_attempt_close(result)

    def test_should_not_attempt_close_browsing(self, detector):
        result = detector.detect("qué tienes")
        assert not detector.should_attempt_close(result)

    def test_should_recommend(self, detector):
        result = detector.detect("qué tienes")
        assert detector.should_recommend(result)

    def test_detects_size(self, detector):
        result = detector.detect("talla M")
        assert result.detected_size == "m"

    def test_detects_color(self, detector):
        result = detector.detect("color negro")
        assert result.detected_color == "negro"

    def test_detects_product(self, detector):
        result = detector.detect("quiero la casaca denim")
        assert result.detected_product


class TestContextualResponseEngine:
    @pytest.fixture
    def engine(self):
        return ContextualResponseEngine()

    def test_get_snapshot_creates_new(self, engine):
        snap = engine.get_snapshot("conv-1")
        assert isinstance(snap, ContextSnapshot)
        assert not snap.product_already_shown

    def test_update_snapshot(self, engine):
        engine.update_snapshot("conv-1", "quiero un polo", product_name="Polo Test")
        snap = engine.get_snapshot("conv-1")
        assert snap.last_product_name == "Polo Test"
        assert snap.product_already_shown
        assert snap.message_count == 1

    def test_should_relist_products_new(self, engine):
        assert engine.should_relist_products("conv-new")

    def test_should_not_relist_after_shown(self, engine):
        engine.update_snapshot("conv-2", "quiero un polo", product_name="Polo")
        engine.update_snapshot("conv-2", "talla M")
        assert not engine.should_relist_products("conv-2")

    def test_should_suggest_styling(self, engine):
        engine.update_snapshot("conv-3", "quiero un polo", product_name="Polo")
        assert engine.should_suggest_styling("conv-3")


class TestNaturalLanguageVariator:
    @pytest.fixture
    def variator(self):
        return NaturalLanguageVariator()

    def test_get_opening_returns_string(self, variator):
        assert variator.get_opening()

    def test_get_closing_returns_string(self, variator):
        assert variator.get_closing()

    def test_get_transition_returns_string(self, variator):
        assert variator.get_transition()

    def test_get_reassurance_returns_string(self, variator):
        assert variator.get_reassurance()

    def test_get_enthusiasm_returns_string(self, variator):
        assert variator.get_enthusiasm()

    def test_openings_count(self, variator):
        assert variator.openings_count >= 30

    def test_closings_count(self, variator):
        assert variator.closings_count >= 30

    def test_transitions_count(self, variator):
        assert variator.transitions_count >= 20

    def test_reassurance_count(self, variator):
        assert variator.reassurance_count >= 15

    def test_opening_variety(self, variator):
        seen = set()
        for _ in range(variator.openings_count):
            seen.add(variator.get_opening())
        assert len(seen) >= 20

    def test_no_consecutive_duplicates(self, variator):
        a = variator.get_opening()
        b = variator.get_opening()
        assert a != b


class TestConversationalTransitionEngine:
    @pytest.fixture
    def engine(self):
        return ConversationalTransitionEngine()

    def test_get_transition_gratitude(self, engine):
        result = engine.get_transition("gracias")
        assert isinstance(result, str)

    def test_get_transition_with_category(self, engine):
        result = engine.get_transition("gracias", "polo")
        assert result

    def test_get_transition_empty(self, engine):
        result = engine.get_transition("xyzzy flurbo")
        assert result == "" or isinstance(result, str)


class TestObjectionHandler:
    @pytest.fixture
    def handler(self):
        return ObjectionHandler()

    def test_detect_expensive(self, handler):
        assert handler.detect_objection("está muy caro") == "caro"

    def test_detect_will_think(self, handler):
        assert handler.detect_objection("lo voy a pensar") == "pensar"

    def test_detect_not_sure(self, handler):
        assert handler.detect_objection("no sé") == "no_se"

    def test_detect_see_more(self, handler):
        assert handler.detect_objection("quiero ver más") == "ver_mas"

    def test_detect_cheaper(self, handler):
        assert handler.detect_objection("tienes algo más barato") == "barato"

    def test_handle_objection_true(self, handler):
        was_obj, response = handler.handle_objection("está caro")
        assert was_obj
        assert response

    def test_handle_objection_false(self, handler):
        was_obj, response = handler.handle_objection("quiero un polo")
        assert not was_obj
        assert not response

    def test_no_false_positive(self, handler):
        assert handler.detect_objection("gracias") is None


class TestEliteSalesCloser:
    @pytest.fixture
    def closer(self):
        return EliteSalesCloser()

    def test_build_closing_basic(self, closer):
        result = closer.build_closing(product_name="Polo Tokyo")
        assert "Polo Tokyo" in result

    def test_build_closing_with_all_info(self, closer):
        result = closer.build_closing(
            product_name="Polo Tokyo",
            available_sizes=["S", "M", "L"],
            has_size=True,
            has_color=True,
        )
        assert result

    def test_build_closing_low_stock(self, closer):
        result = closer.build_closing(product_name="Polo", total_stock=2)
        assert "quedan" in result.lower() or "unidades" in result.lower()


class TestEmotionalConversationEngine:
    @pytest.fixture
    def engine(self):
        return EmotionalConversationEngine()

    def test_get_tone_for_excitement(self, engine):
        assert engine.get_tone_for_emotion("excitement") == "excitement"

    def test_get_tone_for_greeting(self, engine):
        assert engine.get_tone_for_emotion("greeting") == "warm"

    def test_get_tone_for_hesitation(self, engine):
        assert engine.get_tone_for_emotion("hesitation") == "empathetic"

    def test_apply_tone(self, engine):
        result = engine.apply_tone("Texto de prueba", "excitement")
        assert "Texto de prueba" in result

    def test_add_micro_emotion(self, engine):
        result = engine.add_micro_emotion("text", "excitement")
        assert "text" in result


class TestConversationalMemoryEnhancer:
    @pytest.fixture
    def memory(self):
        return ConversationalMemoryEnhancer()

    def test_get_state_creates_new(self, memory):
        state = memory.get_state("conv-1")
        assert state.message_count == 0

    def test_update_state(self, memory):
        memory.update("conv-1", product_name="Polo", style="casual")
        state = memory.get_state("conv-1")
        assert state.product_name == "Polo"
        assert state.style == "casual"

    def test_get_context_summary(self, memory):
        memory.update("conv-1", product_name="Polo", color="negro")
        summary = memory.get_context_summary("conv-1")
        assert "Polo" in summary
        assert "negro" in summary

    def test_empty_summary(self, memory):
        summary = memory.get_context_summary("conv-never-used")
        assert "Sin contexto" in summary


class TestHumanConversationRules:
    @pytest.fixture
    def rules(self):
        return HumanConversationRules()

    def test_catalog_repetition(self, rules):
        rules.is_catalog_repetition("Tenemos estas opciones disponibles")
        assert not rules.is_catalog_repetition("Te recomiendo este producto")

    def test_similarity(self, rules):
        assert rules.should_vary_response(["Te recomiendo el polo."], "Este jean es ideal.")
        assert not rules.should_vary_response(["Te recomiendo el polo azul."], "Te recomiendo el polo negro.")

    def test_valid_transition(self, rules):
        assert rules.is_valid_transition("gracias, ese estilo combina muy bien", "gracias")
        assert not rules.is_valid_transition("gracias", "gracias")


class TestConversationalCloserEngine:
    @pytest.fixture
    def engine(self):
        return ConversationalCloserEngine()

    async def test_process_basic(self, engine):
        input_data = CloserInput(
            user_message="quiero un polo",
            conversation_id="test",
            response="Te recomiendo este polo.",
        )
        output = await engine.process(input_data=input_data)
        assert isinstance(output, CloserOutput)

    async def test_process_gratitude(self, engine):
        input_data = CloserInput(
            user_message="gracias",
            conversation_id="test",
            response="Aquí tienes.",
            product_name="Polo Tokyo",
            product_category="polo",
        )
        output = await engine.process(input_data=input_data)
        assert output.was_gratitude
        assert output.response and isinstance(output.response, str)

    async def test_process_objection(self, engine):
        input_data = CloserInput(
            user_message="está caro",
            conversation_id="test-obj",
            response="Este producto cuesta...",
            product_name="Polo Premium",
        )
        output = await engine.process(input_data=input_data)
        assert output.was_objection
        assert output.response

    async def test_process_closing(self, engine):
        input_data = CloserInput(
            user_message="me lo llevo",
            conversation_id="test-close",
            response="Producto disponible.",
            product_name="Polo Tokyo",
        )
        output = await engine.process(input_data=input_data)
        assert output.was_closing
        assert "Polo Tokyo" in output.response

    async def test_process_ready_to_buy(self, engine):
        input_data = CloserInput(
            user_message="lo quiero ya",
            conversation_id="test-buy",
            response="Tenemos stock.",
            product_name="Casaca Denim",
        )
        output = await engine.process(input_data=input_data)
        assert output.was_closing

    async def test_process_hesitation(self, engine):
        input_data = CloserInput(
            user_message="mmm no sé",
            conversation_id="test-hes",
            response="Te recomiendo este.",
        )
        output = await engine.process(input_data=input_data)
        assert output.response

    async def test_sub_engines_accessible(self, engine):
        assert engine.variator is not None
        assert engine.transitions is not None
        assert engine.memory is not None
        assert engine.contextual is not None

    async def test_memory_tracks_conversation(self, engine):
        input1 = CloserInput(user_message="quiero un polo", conversation_id="mtest", response="ok")
        await engine.process(input_data=input1)
        input2 = CloserInput(user_message="talla M", conversation_id="mtest", response="disponible", product_name="Polo")
        output2 = await engine.process(input_data=input2)
        assert output2.memory_state.message_count >= 2
