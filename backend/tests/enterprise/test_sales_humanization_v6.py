import pytest

from app.smart_sales.contextual_commitment.selected_product_tracker import (
    CommitmentData,
    CommitmentLevel,
)
from app.smart_sales.entity_extractor import EntityExtractor
from app.smart_sales.humanization.sales_humanization_v6 import (
    PurchaseStage,
    SalesHumanizationV6,
)
from app.smart_sales.product_matcher import MatchedProduct, MatchedVariant


FORBIDDEN_AFTER_SELECTION = (
    "aquí tienes más productos",
    "mira estas opciones",
    "tenemos estas opciones",
    "catálogo completo",
    "lista de productos",
    "gracias por preguntar, estoy aquí para ayudarte",
)


def product(name: str = "Polo Premium Black") -> MatchedProduct:
    return MatchedProduct(
        product_id="prod-1",
        name=name,
        category="Polos",
        base_price=149,
        score=96,
        match_reason="qa",
        available_variants=[
            MatchedVariant(
                variant_id="var-1",
                talla="M",
                color="Azul",
                price=149,
                stock=8,
                reserved_stock=0,
                sku="POLO-BLUE-M",
            )
        ],
    )


def committed(
    *,
    selected_product: str = "Polo Premium Black",
    color: str | None = None,
    size: str | None = None,
    reserved: bool = False,
) -> CommitmentData:
    return CommitmentData(
        selected_product=selected_product,
        selected_color=color,
        selected_size=size,
        selected_category="Polos",
        commitment_level=CommitmentLevel.confirmed if size or color or reserved else CommitmentLevel.selected,
        reservation_confirmed=reserved,
    )


class TestSalesHumanizationV6CriticalFlow:
    @pytest.fixture
    def v6(self) -> SalesHumanizationV6:
        return SalesHumanizationV6()

    @pytest.fixture
    def extractor(self) -> EntityExtractor:
        return EntityExtractor()

    def test_color_request_stays_on_selected_product(self, v6, extractor) -> None:
        result = v6.process(
            user_message="solo quiero el azul",
            commitment=committed(),
            entities=extractor.extract("solo quiero el azul"),
            matched_products=[],
        )

        assert result.handled
        assert "Polo Premium Black" in result.response
        assert "Azul" in result.response
        assert "catálogo" not in result.response.lower()

    def test_reservation_uses_active_product_color_and_size(self, v6, extractor) -> None:
        result = v6.process(
            user_message="resérvame",
            commitment=committed(color="Azul", size="M"),
            entities=extractor.extract("resérvame"),
            matched_products=[],
        )

        assert result.handled
        assert result.should_mark_reserved
        assert result.stage == PurchaseStage.ready_to_buy
        assert "Ya quedó reservado" in result.response
        assert "Polo Premium Black" in result.response
        assert "Color: Azul" in result.response
        assert "Talla: M" in result.response
        assert "envío" in result.response or "forma de pago" in result.response

    def test_reservation_without_size_asks_for_size_not_catalog(self, v6, extractor) -> None:
        result = v6.process(
            user_message="resérvame",
            commitment=committed(color="Azul"),
            entities=extractor.extract("resérvame"),
            matched_products=[],
        )

        assert result.handled
        assert not result.should_mark_reserved
        assert "Polo Premium Black" in result.response
        assert "talla" in result.response.lower()
        assert all(pattern not in result.response.lower() for pattern in FORBIDDEN_AFTER_SELECTION)

    def test_gratitude_after_reservation_preserves_reservation(self, v6, extractor) -> None:
        result = v6.process(
            user_message="gracias",
            commitment=committed(color="Azul", size="M", reserved=True),
            entities=extractor.extract("gracias"),
            matched_products=[],
        )

        assert result.handled
        assert "reserva" in result.response.lower()
        assert "Polo Premium Black" in result.response
        assert "sigue guardada" in result.response

    def test_first_product_match_requests_lock(self, v6, extractor) -> None:
        result = v6.process(
            user_message="quiero el Polo Premium Black",
            commitment=CommitmentData(commitment_level=CommitmentLevel.selected),
            entities=extractor.extract("quiero el Polo Premium Black"),
            matched_products=[product()],
        )

        assert result.should_lock_product
        assert result.product_name == "Polo Premium Black"

    def test_quality_score_zero_for_generic_confirmed_reply(self, v6) -> None:
        score = v6.quality_score(
            "Gracias por preguntar, estoy aquí para ayudarte.",
            committed(color="Azul", size="M"),
        )
        assert score == 0


def build_v6_enterprise_scenarios() -> list[tuple[str, CommitmentData, str]]:
    selected_products = [
        "Polo Premium Black",
        "Casaca Oversize Urban",
        "Jean Cargo Street",
        "Blazer Ivory Elite",
        "Vestido Night Satin",
    ]
    messages = [
        "solo quiero el azul",
        "lo quiero en negro",
        "talla M",
        "me queda mejor L",
        "resérvame",
        "quiero separarlo",
        "apártame ese",
        "gracias",
        "muchas gracias",
        "chao",
        "con qué combina",
        "qué outfit me recomiendas",
        "me lo llevo",
        "confírmame el pedido",
        "nada más gracias",
    ]
    scenarios: list[tuple[str, CommitmentData, str]] = []
    for product_name in selected_products:
        for index, message in enumerate(messages):
            scenarios.append(
                (
                    f"{product_name}-{index}",
                    committed(
                        selected_product=product_name,
                        color="Azul" if index % 2 == 0 else None,
                        size="M" if index in {4, 5, 6, 7, 8, 12, 13, 14} else None,
                        reserved=index in {7, 8, 14},
                    ),
                    message,
                )
            )

    # 75 more multi-turn-like variants focused on purchase stages and objections.
    variants = [
        "solo ese color",
        "solo esa talla",
        "lo voy a pensar",
        "no estoy seguro",
        "prefiero azul",
        "hay en M",
        "me gusta ese",
        "dale ese mismo",
        "se ve bien",
        "quiero continuar",
        "cómo pago",
        "hacen delivery",
        "lo paso a recoger",
        "me confirmas stock",
        "gracias por la ayuda",
    ]
    for product_name in selected_products:
        for index, message in enumerate(variants):
            scenarios.append(
                (
                    f"{product_name}-variant-{index}",
                    committed(
                        selected_product=product_name,
                        color="Negro" if index % 3 == 0 else "Azul",
                        size="M" if index % 4 == 0 else None,
                        reserved=index in {10, 11, 12, 14},
                    ),
                    message,
                )
            )
    return scenarios


@pytest.mark.parametrize("scenario_id,commitment,message", build_v6_enterprise_scenarios())
def test_sales_humanization_v6_150_enterprise_scenarios(
    scenario_id: str,
    commitment: CommitmentData,
    message: str,
) -> None:
    scenarios = build_v6_enterprise_scenarios()
    assert len(scenarios) == 150

    v6 = SalesHumanizationV6()
    extractor = EntityExtractor()
    result = v6.process(
        user_message=message,
        commitment=commitment,
        entities=extractor.extract(message),
        matched_products=[product(commitment.selected_product or "Polo Premium Black")],
    )

    if result.handled:
        response = result.response.lower()
        assert commitment.selected_product.lower() in response or "reserva" in response
        assert all(pattern not in response for pattern in FORBIDDEN_AFTER_SELECTION), scenario_id
        assert v6.quality_score(result.response, commitment) > 0, scenario_id
