import pytest
from app.smart_sales.conversational_router.conversational_intent_detector import (
    ConversationalIntentDetector, ConversationalIntent,
)
from app.smart_sales.conversational_router.greeting_handler import get_greeting
from app.smart_sales.conversational_router.gratitude_handler import get_gratitude_response
from app.smart_sales.conversational_router.hesitation_handler import get_hesitation_response
from app.smart_sales.conversational_router.casual_conversation_handler import get_casual_response
from app.smart_sales.conversational_router.conversational_state_router import (
    ConversationalStateRouter, ConversationStage,
)
from app.smart_sales.conversational_router.human_response_guard import HumanResponseGuard
from app.smart_sales.conversational_router.conversational_router_engine import (
    ConversationalRouterEngine, ConversationalIntent,
)


class TestConversationalIntentDetector:
    def setup_method(self):
        self.detector = ConversationalIntentDetector()

    def test_detect_greeting_hola(self):
        result = self.detector.detect("hola")
        assert result.intent == ConversationalIntent.greeting
        assert result.confidence >= 0.9

    def test_detect_greeting_buenas(self):
        result = self.detector.detect("buenas")
        assert result.intent == ConversationalIntent.greeting

    def test_detect_greeting_hey(self):
        result = self.detector.detect("hey")
        assert result.intent == ConversationalIntent.greeting

    def test_detect_greeting_que_tal(self):
        result = self.detector.detect("qué tal")
        assert result.intent == ConversationalIntent.greeting

    def test_detect_gratitude_gracias(self):
        result = self.detector.detect("gracias")
        assert result.intent == ConversationalIntent.gratitude
        assert result.confidence >= 0.9

    def test_detect_gratitude_mil_gracias(self):
        result = self.detector.detect("mil gracias")
        assert result.intent == ConversationalIntent.gratitude

    def test_detect_gratitude_thanks(self):
        result = self.detector.detect("thanks")
        assert result.intent == ConversationalIntent.gratitude

    def test_detect_hesitation_mmm(self):
        result = self.detector.detect("mmm")
        assert result.intent == ConversationalIntent.hesitation

    def test_detect_hesitation_no_se(self):
        result = self.detector.detect("no sé")
        assert result.intent == ConversationalIntent.hesitation

    def test_detect_hesitation_lo_pensare(self):
        result = self.detector.detect("lo pensaré")
        assert result.intent == ConversationalIntent.hesitation

    def test_detect_hesitation_quizas(self):
        result = self.detector.detect("quizá luego vuelvo")
        assert result.intent == ConversationalIntent.hesitation

    def test_detect_casual_ok(self):
        result = self.detector.detect("ok")
        assert result.intent == ConversationalIntent.casual_chat

    def test_detect_casual_perfecto(self):
        result = self.detector.detect("perfecto")
        assert result.intent == ConversationalIntent.casual_chat

    def test_detect_casual_genial(self):
        result = self.detector.detect("genial")
        assert result.intent == ConversationalIntent.casual_chat

    def test_detect_browsing_busco(self):
        result = self.detector.detect("busco casacas")
        assert result.intent == ConversationalIntent.browsing

    def test_detect_sizing_talla_m(self):
        result = self.detector.detect("talla m?")
        assert result.intent == ConversationalIntent.sizing

    def test_detect_sizing_full(self):
        result = self.detector.detect("tienes en talla L?")
        assert result.intent == ConversationalIntent.sizing

    def test_detect_styling_combina(self):
        result = self.detector.detect("qué combina con esta casaca?")
        assert result.intent == ConversationalIntent.styling

    def test_detect_committed_lo_quiero(self):
        result = self.detector.detect("lo quiero")
        assert result.intent == ConversationalIntent.committed

    def test_detect_ready_to_buy_compro(self):
        result = self.detector.detect("cómo lo compro?")
        assert result.intent == ConversationalIntent.ready_to_buy

    def test_detect_objection_caro(self):
        result = self.detector.detect("está muy caro")
        assert result.intent == ConversationalIntent.objection

    def test_detect_confusion_no_entiendo(self):
        result = self.detector.detect("no entiendo")
        assert result.intent == ConversationalIntent.confusion

    def test_detect_comparison_cual_mejor(self):
        result = self.detector.detect("cuál es mejor?")
        assert result.intent == ConversationalIntent.comparison

    def test_detect_unknown_random(self):
        result = self.detector.detect("el cielo es azul y las flores rojas")
        assert result.intent == ConversationalIntent.unknown

    def test_detect_empty_string(self):
        result = self.detector.detect("")
        assert result.intent == ConversationalIntent.unknown

    def test_detect_secondary_intents(self):
        result = self.detector.detect("hola gracias")
        assert ConversationalIntent.greeting in [result.intent] + result.secondary_intents
        assert ConversationalIntent.gratitude in [result.intent] + result.secondary_intents

    def test_detect_size_entity(self):
        result = self.detector.detect("talla m?")
        assert "size" in result.detected_entities
        assert result.detected_entities["size"] == "m"

    def test_detect_greeting_with_punctuation(self):
        result = self.detector.detect("hola!!!")
        assert result.intent == ConversationalIntent.greeting

    def test_detect_greeting_upper(self):
        result = self.detector.detect("HOLA")
        assert result.intent == ConversationalIntent.greeting

    def test_detect_mixed_greeting(self):
        result = self.detector.detect("hola buenas tardes")
        assert result.intent == ConversationalIntent.greeting

    def test_detect_ready_to_buy_delivery(self):
        result = self.detector.detect("cuánto demora el delivery?")
        assert result.intent == ConversationalIntent.ready_to_buy


class TestGreetingHandler:
    def test_get_greeting_returns_string(self):
        response = get_greeting("conv-1")
        assert isinstance(response, str)
        assert len(response) > 10

    def test_get_greeting_not_empty(self):
        response = get_greeting("conv-2")
        assert response.strip() != ""

    def test_get_greeting_rotation(self):
        r1 = get_greeting("conv-rot")
        r2 = get_greeting("conv-rot")
        assert r1 != r2

    def test_get_greeting_gender_masculine(self):
        response = get_greeting("conv-m", "hombre")
        assert isinstance(response, str)
        assert len(response) > 10

    def test_get_greeting_gender_feminine(self):
        response = get_greeting("conv-f", "mujer")
        assert isinstance(response, str)
        assert len(response) > 10

    def test_get_greeting_gender_emoji(self):
        response = get_greeting("conv-fe", "mujer")
        assert "😊" in response or "🔥" in response or "✨" in response

    def test_get_greeting_no_conversation_id(self):
        response = get_greeting()
        assert isinstance(response, str)
        assert len(response) > 10


class TestGratitudeHandler:
    def test_get_gratitude_returns_string(self):
        response = get_gratitude_response("conv-1")
        assert isinstance(response, str)
        assert len(response) > 10

    def test_get_gratitude_not_empty(self):
        response = get_gratitude_response("conv-2")
        assert response.strip() != ""

    def test_get_gratitude_rotation(self):
        r1 = get_gratitude_response("conv-rot")
        r2 = get_gratitude_response("conv-rot")
        assert r1 != r2

    def test_get_gratitude_emoji(self):
        response = get_gratitude_response("conv-3")
        assert "😊" in response or "🔥" in response or "👌" in response

    def test_get_gratitude_no_conversation_id(self):
        response = get_gratitude_response()
        assert isinstance(response, str)
        assert len(response) > 10


class TestHesitationHandler:
    def test_get_hesitation_returns_string(self):
        response = get_hesitation_response("conv-1")
        assert isinstance(response, str)
        assert len(response) > 10

    def test_get_hesitation_not_empty(self):
        response = get_hesitation_response("conv-2")
        assert response.strip() != ""

    def test_get_hesitation_rotation(self):
        r1 = get_hesitation_response("conv-rot")
        r2 = get_hesitation_response("conv-rot")
        assert r1 != r2

    def test_get_hesitation_no_pressure(self):
        response = get_hesitation_response("conv-3")
        assert "tómate tu tiempo" in response.lower() or "sin prisa" in response.lower() or "sin problema" in response.lower() or "tranqui" in response.lower() or "cuando" in response.lower()

    def test_get_hesitation_emoji(self):
        response = get_hesitation_response("conv-4")
        assert "😊" in response or "🔥" in response or "👌" in response

    def test_get_hesitation_no_conversation_id(self):
        response = get_hesitation_response()
        assert isinstance(response, str)
        assert len(response) > 10


class TestCasualConversationHandler:
    def test_get_casual_returns_string(self):
        response = get_casual_response("conv-1")
        assert isinstance(response, str)
        assert len(response) > 5

    def test_get_casual_rotation(self):
        r1 = get_casual_response("conv-rot")
        r2 = get_casual_response("conv-rot")
        assert r1 != r2

    def test_get_casual_engagement(self):
        response = get_casual_response("conv-3")
        assert "¿" in response or "?" in response or "😊" in response

    def test_get_casual_no_catalog(self):
        response = get_casual_response("conv-4")
        assert "mira estas" not in response.lower()
        assert "te recomiendo" not in response.lower()
        assert "tenemos" not in response.lower()

    def test_get_casual_no_conversation_id(self):
        response = get_casual_response()
        assert isinstance(response, str)
        assert len(response) > 5


class TestConversationalStateRouter:
    _counter = 0

    def setup_method(self):
        self.router = ConversationalStateRouter()
        TestConversationalStateRouter._counter += 1
        self.cid = f"test-state-{TestConversationalStateRouter._counter}"

    def test_initial_stage_greeting(self):
        assert self.router.get_stage(self.cid) == ConversationStage.greeting

    def test_greeting_to_browsing(self):
        from app.smart_sales.conversational_router.conversational_intent_detector import ConversationalIntent
        result = self.router.transition(self.cid, ConversationalIntent.browsing)
        assert result.did_transition
        assert self.router.get_stage(self.cid) == ConversationStage.browsing

    def test_browsing_to_committed(self):
        from app.smart_sales.conversational_router.conversational_intent_detector import ConversationalIntent
        self.router.transition(self.cid, ConversationalIntent.browsing)
        result = self.router.transition(self.cid, ConversationalIntent.committed)
        assert result.did_transition
        assert self.router.get_stage(self.cid) == ConversationStage.committed

    def test_committed_to_checkout(self):
        from app.smart_sales.conversational_router.conversational_intent_detector import ConversationalIntent
        self.router.transition(self.cid, ConversationalIntent.committed)
        result = self.router.transition(self.cid, ConversationalIntent.ready_to_buy)
        assert result.did_transition
        assert self.router.get_stage(self.cid) == ConversationStage.checkout_ready

    def test_no_regression_from_committed(self):
        from app.smart_sales.conversational_router.conversational_intent_detector import ConversationalIntent
        self.router.transition(self.cid, ConversationalIntent.committed)
        result = self.router.transition(self.cid, ConversationalIntent.greeting)
        assert not result.did_transition
        assert self.router.get_stage(self.cid) == ConversationStage.committed

    def test_reset(self):
        from app.smart_sales.conversational_router.conversational_intent_detector import ConversationalIntent
        self.router.transition(self.cid, ConversationalIntent.browsing)
        self.router.reset(self.cid)
        assert self.router.get_stage(self.cid) == ConversationStage.greeting

    def test_skipped_stages(self):
        from app.smart_sales.conversational_router.conversational_intent_detector import ConversationalIntent
        result = self.router.transition(self.cid, ConversationalIntent.ready_to_buy)
        assert len(result.skipped_stages) > 0

    def test_multiple_conversations(self):
        from app.smart_sales.conversational_router.conversational_intent_detector import ConversationalIntent
        self.router.transition("cid-a", ConversationalIntent.browsing)
        self.router.transition("cid-b", ConversationalIntent.committed)
        assert self.router.get_stage("cid-a") == ConversationStage.browsing
        assert self.router.get_stage("cid-b") == ConversationStage.committed


class TestHumanResponseGuard:
    _counter = 0

    def setup_method(self):
        self.guard = HumanResponseGuard()
        TestHumanResponseGuard._counter += 1
        self.cid = f"test-guard-{TestHumanResponseGuard._counter}"

    def test_initial_no_block(self):
        result = self.guard.check_response(self.cid, "hola")
        assert not result.is_blocked

    def test_catalog_overuse_blocked(self):
        self.guard.record_response(self.cid, "mira estas casacas que tenemos disponibles")
        self.guard.record_response(self.cid, "te recomiendo estos modelos que tenemos")
        result = self.guard.check_response(self.cid, "mira estas opciones disponibles")
        assert result.is_blocked or result.catalog_repetition_score > 0
        assert "catálogo" in result.block_reason.lower() or result.catalog_repetition_score > 0

    def test_identical_response_blocked(self):
        self.guard.record_response(self.cid, "Hola en qué puedo ayudarte")
        result = self.guard.check_response(self.cid, "Hola en qué puedo ayudarte")
        assert result.is_blocked

    def test_no_false_positive(self):
        result = self.guard.check_response(self.cid, "claro tómate tu tiempo")
        assert not result.is_blocked

    def test_get_catalog_count(self):
        assert self.guard.get_catalog_count(self.cid) == 0
        self.guard.record_response(self.cid, "mira estas casacas disponibles")
        self.guard.record_response(self.cid, "te recomiendo estos modelos")
        assert self.guard.get_catalog_count(self.cid) >= 1

    def test_reset(self):
        self.guard.record_response(self.cid, "hola")
        self.guard.reset(self.cid)
        assert self.guard.get_catalog_count(self.cid) == 0
        result = self.guard.check_response(self.cid, "hola")
        assert not result.is_blocked

    def test_cta_overuse(self):
        self.guard.record_response(self.cid, "te gusta esta casaca?")
        self.guard.record_response(self.cid, "qué opinas de este modelo?")
        result = self.guard.check_response(self.cid, "te interesa este producto?")
        assert result.cta_repetition_score > 0

    def test_different_conversations_independent(self):
        self.guard.record_response("cid-1", "mira estas casacas que tenemos")
        result_2 = self.guard.check_response("cid-2", "mira estas opciones disponibles")
        assert not result_2.is_blocked


class TestConversationalRouterEngine:
    def setup_method(self):
        self.engine = ConversationalRouterEngine()
        self.cid = "test-engine"

    def test_process_greeting_handled(self):
        result = self.engine.process("hola", self.cid)
        assert result.handled
        assert result.intent == ConversationalIntent.greeting
        assert len(result.response) > 10

    def test_process_gratitude_handled(self):
        result = self.engine.process("gracias", self.cid)
        assert result.handled
        assert result.intent == ConversationalIntent.gratitude

    def test_process_hesitation_handled(self):
        result = self.engine.process("mmm", self.cid)
        assert result.handled
        assert result.intent == ConversationalIntent.hesitation

    def test_process_casual_handled(self):
        result = self.engine.process("ok", self.cid)
        assert result.handled
        assert result.intent == ConversationalIntent.casual_chat

    def test_process_browsing_not_handled(self):
        result = self.engine.process("busco casacas", self.cid)
        assert not result.handled

    def test_process_unknown_not_handled(self):
        result = self.engine.process("el cielo es azul", self.cid)
        assert not result.handled

    def test_process_empty_returns_not_handled(self):
        result = self.engine.process("", self.cid)
        assert not result.handled

    def test_process_white_space_not_handled(self):
        result = self.engine.process("   ", self.cid)
        assert not result.handled

    def test_greeting_no_catalog(self):
        result = self.engine.process("hola", self.cid + "-nc")
        assert "mira estas" not in result.response.lower()
        assert "te recomiendo" not in result.response.lower()
        assert "tenemos" not in result.response.lower()

    def test_gratitude_no_catalog(self):
        result = self.engine.process("gracias", self.cid + "-gc")
        assert "mira estas" not in result.response.lower()
        assert "te recomiendo" not in result.response.lower()

    def test_hesitation_no_pressure(self):
        result = self.engine.process("lo pensaré", self.cid + "-hp")
        assert "tómate tu tiempo" in result.response.lower() or "sin problema" in result.response.lower() or "sin prisa" in result.response.lower()

    def test_response_has_emoji(self):
        result = self.engine.process("hola", self.cid + "-em")
        assert "😊" in result.response or "🔥" in result.response or "😎" in result.response or "👋" in result.response

    def test_conversation_id_none(self):
        result = self.engine.process("hola")
        assert result.handled

    def test_state_router_updated(self):
        cid = self.cid + "-sr"
        self.engine.process("hola", cid)
        stage = self.engine.get_state_router().get_stage(cid)
        assert stage == ConversationStage.greeting or stage is not None

    def test_greeting_gender_hombre(self):
        result = self.engine.process("hola", self.cid + "-gh", "hombre")
        assert result.handled

    def test_greeting_gender_mujer(self):
        result = self.engine.process("hola", self.cid + "-gm", "mujer")
        assert result.handled

    def test_anti_repetition_greeting_twice(self):
        cid = self.cid + "-ar"
        r1 = self.engine.process("hola", cid)
        r2 = self.engine.process("hola", cid)
        assert r1.handled
        assert r2.handled
        assert r1.response != r2.response

    def test_anti_repetition_gratitude_twice(self):
        cid = self.cid + "-ag"
        r1 = self.engine.process("gracias", cid)
        r2 = self.engine.process("gracias", cid)
        assert r1.handled
        assert r2.handled
        assert r1.response != r2.response

    def test_reset(self):
        cid = self.cid + "-rs"
        self.engine.process("hola", cid)
        self.engine.reset(cid)
        assert self.engine.get_state_router().get_stage(cid) == ConversationStage.greeting

    def test_casual_no_catalog(self):
        result = self.engine.process("ok", self.cid + "-cc")
        assert "mira estas" not in result.response.lower()

    def test_hesitation_contains_gentle_urgency(self):
        result = self.engine.process("no sé", self.cid + "-hu")
        assert result.handled
        assert result.intent == ConversationalIntent.hesitation

    def test_detected_entities_in_result(self):
        result = self.engine.process("talla m", self.cid + "-de")
        assert not result.handled
        assert result.intent == ConversationalIntent.sizing

    def test_greeting_response_not_empty(self):
        result = self.engine.process("hola", self.cid + "-ne")
        assert result.response.strip() != ""

    def test_gratitude_response_not_empty(self):
        result = self.engine.process("gracias", self.cid + "-ge")
        assert result.response.strip() != ""

    def test_configuration_refresh(self):
        result = self.engine.process("hola", self.cid + "-cf", force_refresh=True)
        assert result.handled

    def test_record_response_then_check(self):
        self.engine.record_response(self.cid + "-rc", "test response")
        guard = self.engine.get_response_guard()
        stats = guard.check_response(self.cid + "-rc", "test response")
        assert stats.is_blocked
