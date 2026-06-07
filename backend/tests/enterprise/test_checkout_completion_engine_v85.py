import pytest

from app.smart_sales.contextual_commitment.selected_product_tracker import (
    CommitmentData,
    CommitmentLevel,
)
from app.smart_sales.entity_extractor import EntityExtractor
from app.smart_sales.order_flow_engine import OrderFlowEngine, OrderState


FORBIDDEN_ACTIVE_PURCHASE = (
    "cómo estás",
    "como estas",
    "catálogo",
    "catalogo",
    "mira estas opciones",
    "te recomiendo",
    "en qué puedo ayudarte",
    "aquí tienes",
    "está saliendo muchísimo",
    "prenda premium",
)


def commitment(product: str, size: str | None = "M", color: str | None = None) -> CommitmentData:
    return CommitmentData(
        selected_product=product,
        selected_size=size,
        selected_color=color,
        selected_category="Polos",
        commitment_level=CommitmentLevel.confirmed if size else CommitmentLevel.selected,
    )


def build_300_checkout_scenarios() -> list[tuple[str, list[str], OrderState]]:
    products = [
        "Polo Premium Black",
        "Casaca Oversize Urban",
        "Jean Cargo Street",
        "Blazer Ivory Elite",
        "Vestido Night Satin",
        "Hoodie Minimal Sand",
        "Camisa Oxford White",
        "Zapatilla Runner Pro",
        "Pantalon Tailored Grey",
        "Polo Sport White",
    ]
    confirmations = ["si", "sí", "ok", "dale", "correcto", "perfecto", "lo quiero", "me interesa", "resérvamelo", "comprar"]
    payment = ["al contado", "efectivo", "transferencia", "yape", "plin"]
    delivery = ["delivery", "envíame a casa", "a casa", "envío a casa", "domicilio"]
    pickup = ["tienda", "recojo", "recojo en tienda", "lo paso a recoger", "retiro en local"]
    addresses = ["San Isidro", "Miraflores", "Av Primavera 120", "Surco", "Calle Lima 450"]
    names = ["Julio", "María", "Carlos", "Ana López", "Luis Pérez"]

    scenarios: list[tuple[str, list[str], OrderState]] = []
    for product in products:
        for msg in confirmations:
            scenarios.append((f"{product}-confirm-{msg}", [msg], OrderState.RESERVATION_PENDING))
        for msg in payment:
            scenarios.append((f"{product}-payment-{msg}", [msg], OrderState.DELIVERY_PENDING))
        for msg in delivery:
            scenarios.append((f"{product}-delivery-{msg}", ["si", msg], OrderState.ADDRESS_PENDING))
        for msg in pickup:
            scenarios.append((f"{product}-pickup-{msg}", ["si", msg], OrderState.CUSTOMER_NAME_PENDING))
        for msg in addresses:
            scenarios.append((f"{product}-address-{msg}", ["si", "delivery", msg], OrderState.CUSTOMER_NAME_PENDING))
        for msg in names:
            scenarios.append((f"{product}-name-{msg}", ["si", "tienda", msg], OrderState.ORDER_CONFIRMED))

    assert len(scenarios) >= 300
    return scenarios


@pytest.mark.parametrize("scenario_id,messages,expected_state", build_300_checkout_scenarios())
def test_checkout_completion_engine_v85_300_enterprise_scenarios(
    scenario_id: str,
    messages: list[str],
    expected_state: OrderState,
) -> None:
    engine = OrderFlowEngine()
    extractor = EntityExtractor()
    product = scenario_id.split("-")[0]
    data = commitment(product=product)
    conv_id = scenario_id

    result = None
    for message in messages:
        result = engine.process(
            conversation_id=conv_id,
            user_message=message,
            commitment=data,
            entities=extractor.extract(message),
        )
        assert result.handled, scenario_id
        response = result.response.lower()
        assert all(pattern not in response for pattern in FORBIDDEN_ACTIVE_PURCHASE), scenario_id
        if engine.is_catalog_forbidden(conv_id):
            assert engine.quality_score(conv_id, result.response) == 100, scenario_id

    assert result is not None
    assert result.state == expected_state, scenario_id


def test_checkout_completion_engine_v85_real_success_conversation() -> None:
    engine = OrderFlowEngine()
    extractor = EntityExtractor()
    data = commitment(product="Polo Premium Black", size="M")
    conv_id = "success-flow"

    turns = [
        ("M", OrderState.RESERVATION_PENDING),
        ("Delivery", OrderState.ADDRESS_PENDING),
        ("San Isidro", OrderState.CUSTOMER_NAME_PENDING),
        ("Julio", OrderState.ORDER_CONFIRMED),
    ]
    last = None
    for message, state in turns:
        last = engine.process(
            conversation_id=conv_id,
            user_message=message,
            commitment=data,
            entities=extractor.extract(message),
        )
        assert last.state == state
        assert "catálogo" not in last.response.lower()

    assert last is not None
    assert "Pedido confirmado" in last.response
    assert "Producto: Polo Premium Black" in last.response
    assert "Talla: M" in last.response
    assert "Entrega: Delivery - San Isidro" in last.response
    assert "Cliente: Julio" in last.response
