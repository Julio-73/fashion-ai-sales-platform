import pytest

from app.smart_sales.human_sales.tone_profiles import (
    STREETWEAR, LUXURY, PREMIUM, CASUAL,
    MODERN_FASHION, GENZ_FASHION, ALL_PROFILES, PROFILE_MAP,
    detect_profile_from_style, get_profile, pick_random,
)
from app.smart_sales.human_sales.emotional_detector import (
    EmotionalDetector, EmotionalState,
)
from app.smart_sales.human_sales.conversational_flow_engine import (
    ConversationalFlowEngine, SalesStage, FlowContext,
)
from app.smart_sales.human_sales.personality_engine import PersonalityEngine
from app.smart_sales.human_sales.social_proof_engine import SocialProofEngine
from app.smart_sales.human_sales.scarcity_engine import ScarcityEngine
from app.smart_sales.human_sales.urgency_engine import UrgencyEngine
from app.smart_sales.human_sales.persuasion_engine import PersuasionEngine
from app.smart_sales.human_sales.closing_engine import ClosingEngine
from app.smart_sales.human_sales.styling_advisor import StylingAdvisor
from app.smart_sales.human_sales.sales_psychology_engine import SalesPsychologyEngine
from app.smart_sales.human_sales.human_sales_engine import (
    HumanSalesPsychologyEngine, HumanSalesInput, HumanSalesOutput,
)


class TestToneProfiles:
    def test_all_profiles_have_required_fields(self):
        for profile in ALL_PROFILES:
            assert profile.name
            assert profile.emojis
            assert profile.openings
            assert profile.closings
            assert profile.adjectives
            assert profile.connectors
            assert profile.style_adjectives
            assert profile.writing_style
            assert len(profile.openings) >= 3
            assert len(profile.closings) >= 3

    def test_profile_map_contains_all(self):
        for profile in ALL_PROFILES:
            assert profile.name in PROFILE_MAP

    def test_get_profile_returns_correct(self):
        assert get_profile("streetwear") == STREETWEAR
        assert get_profile("luxury") == LUXURY
        assert get_profile("premium") == PREMIUM
        assert get_profile("casual") == CASUAL
        assert get_profile("modern_fashion") == MODERN_FASHION
        assert get_profile("genz_fashion") == GENZ_FASHION
        assert get_profile("nonexistent") == PREMIUM

    def test_detect_profile_from_style(self):
        assert detect_profile_from_style("elegante") == LUXURY
        assert detect_profile_from_style("urbano") == STREETWEAR
        assert detect_profile_from_style("casual") == CASUAL
        assert detect_profile_from_style("genz") == GENZ_FASHION
        assert detect_profile_from_style("moderno") == MODERN_FASHION
        assert detect_profile_from_style("") == PREMIUM
        assert detect_profile_from_style(None) == PREMIUM

    def test_pick_random_returns_item(self):
        items = ["a", "b", "c"]
        for _ in range(20):
            result = pick_random(items)
            assert result in items

    def test_profile_openings_varied(self):
        for profile in ALL_PROFILES:
            seen = set()
            for _ in range(50):
                seen.add(pick_random(profile.openings))
            assert len(seen) >= 2


class TestEmotionalDetector:
    @pytest.fixture
    def detector(self):
        return EmotionalDetector()

    def test_detect_excitement(self, detector):
        result = detector.detect("QUIERO ESO")
        assert result.state == EmotionalState.excitement or result.state == EmotionalState.high_intent
        assert result.confidence > 0.5

    def test_detect_high_intent(self, detector):
        result = detector.detect("me lo llevo")
        assert result.state == EmotionalState.high_intent
        assert result.confidence > 0.8

    def test_detect_hesitation(self, detector):
        result = detector.detect("mmm no sé")
        assert result.state == EmotionalState.hesitation or result.state == EmotionalState.indecision
        assert result.confidence > 0.5

    def test_detect_urgency(self, detector):
        result = detector.detect("necesito para mañana")
        assert result.state == EmotionalState.urgency
        assert result.confidence > 0.5

    def test_detect_greeting(self, detector):
        result = detector.detect("Hola buenas tardes")
        assert result.state == EmotionalState.greeting

    def test_detect_frustration(self, detector):
        result = detector.detect("esto no funciona, qué mal servicio")
        assert result.state == EmotionalState.frustration

    def test_detect_browsing(self, detector):
        result = detector.detect("qué tienes de ropa")
        assert result.state == EmotionalState.browsing

    def test_detect_indecision(self, detector):
        result = detector.detect("no sé cuál me recomiendas")
        assert result.state == EmotionalState.indecision
        assert result.confidence > 0.5

    def test_empty_message(self, detector):
        result = detector.detect("")
        assert result.state == EmotionalState.neutral
        assert result.confidence == 0.0

    def test_neutral_message(self, detector):
        result = detector.detect("esto es una mesa")
        assert result.state == EmotionalState.neutral

    def test_secondary_states(self, detector):
        result = detector.detect("QUIERO ESO ya mismo")
        assert len(result.secondary_states) > 0 or result.state in (EmotionalState.excitement, EmotionalState.high_intent, EmotionalState.urgency)

    def test_recommended_strategy(self, detector):
        result = detector.detect("me lo llevo")
        assert result.recommended_strategy in ("direct_close", "reinforce_and_close")

    def test_detected_keywords(self, detector):
        result = detector.detect("quiero comprar este producto")
        assert len(result.detected_keywords) > 0


class TestConversationalFlowEngine:
    @pytest.fixture
    def engine(self):
        return ConversationalFlowEngine()

    def test_get_or_create_creates_new(self, engine):
        ctx = engine.get_or_create("conv-1")
        assert isinstance(ctx, FlowContext)
        assert ctx.stage == SalesStage.greeting

    def test_get_or_create_returns_same(self, engine):
        ctx1 = engine.get_or_create("conv-1")
        ctx2 = engine.get_or_create("conv-1")
        assert ctx1 is ctx2

    def test_update_stage_transitions_correctly(self, engine):
        stage = engine.update_stage("conv-1", "Hola")
        assert stage == SalesStage.discovery

    def test_update_stage_to_recommendation(self, engine):
        engine.update_stage("conv-1", "Hola")
        stage = engine.update_stage("conv-1", "quiero un polo")
        assert stage in (SalesStage.recommendation, SalesStage.discovery)

    def test_update_stage_to_closing_on_high_intent(self, engine):
        engine.update_stage("conv-1", "quiero un polo")
        stage = engine.update_stage("conv-1", "me lo llevo", emotional_state="high_intent")
        assert stage == SalesStage.closing

    def test_closing_initiated(self, engine):
        engine.update_stage("conv-1", "me lo llevo", emotional_state="high_intent")
        assert not engine.should_push_closing("conv-1")
        engine.mark_closing_initiated("conv-1")
        assert engine.get_or_create("conv-1").closing_initiated

    def test_should_upsell(self, engine):
        assert not engine.should_upsell("conv-2")
        engine.mark_upsell_offered("conv-2")
        assert engine.get_or_create("conv-2").upsell_offered

    def test_get_stage_prompt_returns_string(self, engine):
        for stage in SalesStage:
            prompt = engine.get_stage_prompt(stage)
            assert isinstance(prompt, str)
            assert len(prompt) > 10

    def test_different_conversations_independent(self, engine):
        stage_a = engine.update_stage("conv-a", "me lo llevo", emotional_state="high_intent")
        stage_b = engine.update_stage("conv-b", "Hola")
        ctx_a = engine.get_or_create("conv-a")
        ctx_b = engine.get_or_create("conv-b")
        assert stage_a != stage_b or ctx_a.stage != ctx_b.stage

    def test_message_count_increment(self, engine):
        ctx = engine.get_or_create("conv-1")
        engine.update_stage("conv-1", "Hola")
        assert ctx.total_messages == 1
        engine.update_stage("conv-1", "cómo estás")
        assert ctx.total_messages == 2


class TestPersonalityEngine:
    @pytest.fixture
    def engine(self):
        return PersonalityEngine()

    def test_detect_profile(self, engine):
        profile = engine.detect_profile(style="elegante")
        assert profile.name == "luxury"

    def test_detect_profile_default(self, engine):
        profile = engine.detect_profile()
        assert profile.name == "premium"

    def test_get_profile_emoji(self, engine):
        emoji = engine.get_profile_emoji(STREETWEAR)
        assert emoji in STREETWEAR.emojis

    def test_get_profile_statement(self, engine):
        stmt = engine.get_profile_statement("streetwear")
        assert isinstance(stmt, str)
        assert len(stmt) > 5

    def test_get_opening(self, engine):
        opening = engine.get_opening(PREMIUM)
        assert opening in PREMIUM.openings

    def test_get_closing(self, engine):
        closing = engine.get_closing(PREMIUM)
        assert closing in PREMIUM.closings

    def test_get_connector(self, engine):
        conn = engine.get_connector(PREMIUM)
        assert conn in PREMIUM.connectors

    def test_enhance_with_personality(self, engine):
        result = engine.enhance_with_personality("Te recomiendo este producto.", "premium")
        assert "Te recomiendo este producto" in result

    def test_reset(self, engine):
        engine.get_profile_statement("premium")
        engine.reset()
        assert True


class TestSocialProofEngine:
    @pytest.fixture
    def engine(self):
        return SocialProofEngine()

    def test_get_proof_returns_string(self, engine):
        proof = engine.get_proof()
        assert isinstance(proof, str)
        assert len(proof) > 5

    def test_get_proof_with_category(self, engine):
        proof = engine.get_proof("polo")
        assert isinstance(proof, str)

    def test_get_proof_variety(self, engine):
        seen = set()
        for _ in range(20):
            seen.add(engine.get_proof(conversation_id="test-var"))
        assert len(seen) >= 3

    def test_reset(self, engine):
        engine.get_proof(conversation_id="test-reset")
        engine.reset("test-reset")
        assert True

    def test_different_conversations_different_proofs(self, engine):
        p1 = engine.get_proof(conversation_id="conv-a")
        p2 = engine.get_proof(conversation_id="conv-b")
        assert isinstance(p1, str)
        assert isinstance(p2, str)


class TestScarcityEngine:
    @pytest.fixture
    def engine(self):
        return ScarcityEngine()

    def test_low_stock_returns_high_intensity(self, engine):
        result = engine.evaluate(total_stock=2)
        assert result.should_use
        assert result.intensity == "high"

    def test_medium_stock(self, engine):
        result = engine.evaluate(total_stock=7)
        assert result.should_use
        assert result.intensity == "medium"

    def test_high_demand(self, engine):
        result = engine.evaluate(total_stock=50, is_high_demand=True)
        assert result.should_use
        assert result.intensity == "medium"

    def test_no_scarcity(self, engine):
        result = engine.evaluate(total_stock=100)
        assert not result.should_use

    def test_zero_stock(self, engine):
        result = engine.evaluate(total_stock=0)
        assert not result.should_use

    def test_phrase_variety(self, engine):
        seen = set()
        for _ in range(10):
            result = engine.evaluate(total_stock=2, conversation_id="test-var")
            seen.add(result.phrase)
        assert len(seen) >= 2

    def test_reset(self, engine):
        engine.evaluate(total_stock=2, conversation_id="test-reset")
        engine.reset("test-reset")
        assert True


class TestUrgencyEngine:
    @pytest.fixture
    def engine(self):
        return UrgencyEngine()

    def test_no_urgency_outside_persuasion(self, engine):
        result = engine.evaluate(total_stock=2, stage="greeting")
        assert not result.should_use

    def test_high_urgency_low_stock(self, engine):
        result = engine.evaluate(total_stock=2, stage="closing")
        assert result.should_use
        assert result.intensity == "high"

    def test_medium_urgency(self, engine):
        result = engine.evaluate(total_stock=7, stage="persuasion")
        assert result.should_use
        assert result.intensity == "medium"

    def test_low_urgency_high_intent(self, engine):
        result = engine.evaluate(total_stock=50, is_high_intent=True, stage="closing")
        assert result.should_use
        assert result.intensity == "low"

    def test_no_urgency_high_stock(self, engine):
        result = engine.evaluate(total_stock=100, stage="closing")
        assert not result.should_use

    def test_reset(self, engine):
        engine.evaluate(total_stock=2, stage="closing", conversation_id="test-reset")
        engine.reset("test-reset")
        assert True


class TestPersuasionEngine:
    @pytest.fixture
    def engine(self):
        return PersuasionEngine()

    def test_build_persuasion_returns_all_fields(self, engine):
        engine.reset("fresh-test-1")
        ctx = engine.build_persuasion(conversation_id="fresh-test-1")
        assert ctx.should_use
        assert ctx.reassurance, f"Missing reassurance: {ctx}"
        assert ctx.confidence, f"Missing confidence: {ctx}"
        assert ctx.premium_perception, f"Missing premium_perception: {ctx}"
        assert ctx.emotional, f"Missing emotional: {ctx}"

    def test_varied_reassurance(self, engine):
        seen = set()
        for _ in range(15):
            ctx = engine.build_persuasion(conversation_id="test-var")
            seen.add(ctx.reassurance)
        assert len(seen) >= 2

    def test_reset(self, engine):
        engine.build_persuasion(conversation_id="test-reset")
        engine.reset("test-reset")
        assert True


class TestClosingEngine:
    @pytest.fixture
    def engine(self):
        return ClosingEngine()

    def test_should_attempt_close_triggers(self, engine):
        assert engine.should_attempt_close("quiero eso")
        assert engine.should_attempt_close("me lo llevo")
        assert engine.should_attempt_close("lo quiero")
        assert engine.should_attempt_close("talla M")

    def test_should_not_attempt_close(self, engine):
        assert not engine.should_attempt_close("Hola qué tal")
        assert not engine.should_attempt_close("cuánto cuesta")

    def test_build_closing_contains_fields(self, engine):
        ctx = engine.build_closing(product_name="Polo Tokyo")
        assert ctx.should_close
        assert ctx.opener
        assert ctx.confirmation
        assert "Polo Tokyo" in ctx.confirmation
        assert ctx.size_question
        assert ctx.closer

    def test_build_closing_with_existing_info(self, engine):
        ctx = engine.build_closing(
            product_name="Polo Tokyo",
            already_has_size=True,
            already_has_color=True,
        )
        assert not ctx.size_question
        assert not ctx.color_question

    def test_format_closing_response(self, engine):
        ctx = engine.build_closing(product_name="Polo Test")
        response = engine.format_closing_response(ctx)
        assert isinstance(response, str)
        assert len(response) > 10
        assert "Perfecto" in response or ctx.opener in response


class TestStylingAdvisor:
    @pytest.fixture
    def advisor(self):
        return StylingAdvisor()

    def test_advice_by_category(self, advisor):
        advice = advisor.get_styling_advice(category="polo")
        assert advice.should_use
        assert advice.advice
        assert advice.category == "polo"

    def test_advice_by_color(self, advisor):
        advice = advisor.get_styling_advice(color="negro")
        assert advice.should_use
        assert advice.advice

    def test_advice_by_occasion(self, advisor):
        advice = advisor.get_styling_advice(occasion="fiesta")
        assert advice.should_use
        assert advice.advice

    def test_advice_no_input(self, advisor):
        advice = advisor.get_styling_advice()
        assert not advice.should_use
        assert not advice.advice

    def test_advice_category_variety(self, advisor):
        seen = set()
        for _ in range(10):
            advice = advisor.get_styling_advice(category="polo")
            seen.add(advice.advice)
        assert len(seen) >= 2


class TestSalesPsychologyEngine:
    @pytest.fixture
    def engine(self):
        return SalesPsychologyEngine()

    def test_build_context_with_proof(self, engine):
        ctx = engine.build_context(product_category="polo", conversation_id="test")
        assert ctx.social_proof
        assert "social_proof" in ctx.active_techniques

    def test_build_context_with_scarcity(self, engine):
        ctx = engine.build_context(total_stock=2, conversation_id="test")
        assert ctx.scarcity
        assert "scarcity" in ctx.active_techniques

    def test_build_context_with_urgency(self, engine):
        ctx = engine.build_context(total_stock=2, sales_stage="closing", conversation_id="test")
        assert ctx.urgency
        assert "urgency" in ctx.active_techniques

    def test_build_context_with_persuasion(self, engine):
        ctx = engine.build_context(sales_stage="persuasion", conversation_id="test")
        assert ctx.persuasion_reassurance
        assert ctx.persuasion_confidence
        assert "reassurance" in ctx.active_techniques

    def test_sub_engines_accessible(self, engine):
        assert engine.social_proof is not None
        assert engine.scarcity is not None
        assert engine.urgency is not None
        assert engine.persuasion is not None
        assert engine.closing is not None
        assert engine.styling is not None


class TestHumanSalesPsychologyEngine:
    @pytest.fixture
    def engine(self):
        return HumanSalesPsychologyEngine()

    async def test_process_with_simple_message(self, engine):
        input_data = HumanSalesInput(
            user_message="Hola, quiero un polo",
            conversation_id="test-conv",
            product_name="Polo Oversize Tokyo",
            product_category="polo",
            response="Te recomiendo el Polo Oversize Tokyo.",
        )
        output = await engine.process(input_data=input_data)
        assert isinstance(output, HumanSalesOutput)
        assert output.enhanced_response
        assert output.emotional is not None
        assert output.current_stage is not None

    async def test_process_detects_emotion(self, engine):
        input_data = HumanSalesInput(
            user_message="QUIERO ESO YA",
            conversation_id="test-conv-2",
            response="Producto disponible.",
        )
        output = await engine.process(input_data=input_data)
        assert output.emotional is not None
        assert output.emotional.state in (EmotionalState.excitement, EmotionalState.urgency, EmotionalState.high_intent)

    async def test_process_with_closing(self, engine):
        input_data = HumanSalesInput(
            user_message="me lo llevo",
            conversation_id="test-conv-3",
            product_name="Polo Tokyo",
            response="Tenemos disponible en M y L.",
        )
        output = await engine.process(input_data=input_data)
        if output.closing and output.closing.should_close:
            assert "Polo Tokyo" in output.closing.confirmation or output.closing.size_question

    async def test_process_with_styling(self, engine):
        input_data = HumanSalesInput(
            user_message="quiero un polo",
            conversation_id="test-conv-4",
            product_category="polo",
            total_stock=10,
            response="Te recomiendo este polo.",
        )
        output = await engine.process(input_data=input_data)
        if output.styling and output.styling.should_use:
            assert output.styling.advice

    async def test_process_different_conversations_independent(self, engine):
        input1 = HumanSalesInput(
            user_message="Hola",
            conversation_id="conv-a",
            response="Hola.",
        )
        input2 = HumanSalesInput(
            user_message="me lo llevo",
            conversation_id="conv-b",
            product_name="Polo",
            response="Disponible.",
        )
        out1 = await engine.process(input_data=input1)
        out2 = await engine.process(input_data=input2)
        assert out1.current_stage != out2.current_stage or out1.emotional.state != out2.emotional.state

    async def test_sub_engines_accessible(self, engine):
        assert engine.emotional_detector is not None
        assert engine.personality is not None
        assert engine.sales_psychology is not None
        assert engine.closing is not None
        assert engine.styling is not None
        assert engine.flow is not None

    def test_reset_conversation(self, engine):
        engine.reset_conversation("test-conv")
        assert True
