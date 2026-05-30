from app.smart_sales.contextual_commitment.selected_product_tracker import (
    CommitmentData,
    CommitmentLevel,
)
from app.smart_sales.entity_extractor import EntityExtractor
from app.smart_sales.order_flow_engine import OrderFlowEngine, OrderState


def _commitment(size: str | None = "M") -> CommitmentData:
    return CommitmentData(
        selected_product="Polo Premium Black",
        selected_size=size,
        commitment_level=CommitmentLevel.confirmed if size else CommitmentLevel.selected,
    )


def test_checkout_v85_store_pickup_completion() -> None:
    engine = OrderFlowEngine()
    extractor = EntityExtractor()
    conv_id = "checkout-store"
    commitment = _commitment(size="M")

    reserve = engine.process(
        conversation_id=conv_id,
        user_message="si reservame",
        commitment=commitment,
        entities=extractor.extract("si reservame"),
    )
    assert reserve.handled
    assert reserve.state == OrderState.RESERVATION_PENDING
    assert "Te reservo" in reserve.response
    assert "Polo Premium Black" in reserve.response
    assert "Talla M" in reserve.response

    pickup = engine.process(
        conversation_id=conv_id,
        user_message="tienda",
        commitment=commitment,
        entities=extractor.extract("tienda"),
    )
    assert pickup.handled
    assert pickup.state == OrderState.CUSTOMER_NAME_PENDING
    assert "A nombre de quién" in pickup.response

    confirmed = engine.process(
        conversation_id=conv_id,
        user_message="Julio",
        commitment=commitment,
        entities=extractor.extract("Julio"),
    )
    assert confirmed.handled
    assert confirmed.state == OrderState.ORDER_CONFIRMED
    assert "Pedido confirmado" in confirmed.response
    assert "Producto: Polo Premium Black" in confirmed.response
    assert "Talla: M" in confirmed.response
    assert "Entrega: Recojo en tienda" in confirmed.response
    assert "Cliente: Julio" in confirmed.response
    assert "Tu pedido quedó registrado correctamente" in confirmed.response
    assert not engine.is_catalog_forbidden(conv_id)


def test_checkout_v85_delivery_payment_address_completion() -> None:
    engine = OrderFlowEngine()
    extractor = EntityExtractor()
    conv_id = "checkout-delivery"
    commitment = _commitment(size="M")

    payment = engine.process(
        conversation_id=conv_id,
        user_message="quiero pagar al contado",
        commitment=commitment,
        entities=extractor.extract("quiero pagar al contado"),
    )
    assert payment.handled
    assert payment.state == OrderState.DELIVERY_PENDING
    assert "Método de pago registrado" in payment.response
    assert "Está saliendo" not in payment.response

    delivery = engine.process(
        conversation_id=conv_id,
        user_message="envíame a casa",
        commitment=commitment,
        entities=extractor.extract("envíame a casa"),
    )
    assert delivery.handled
    assert delivery.state == OrderState.ADDRESS_PENDING
    assert "dirección" in delivery.response
    assert "prenda premium" not in delivery.response

    address = engine.process(
        conversation_id=conv_id,
        user_message="San Isidro",
        commitment=commitment,
        entities=extractor.extract("San Isidro"),
    )
    assert address.handled
    assert address.state == OrderState.CUSTOMER_NAME_PENDING
    assert "A nombre de quién" in address.response

    confirmed = engine.process(
        conversation_id=conv_id,
        user_message="Julio",
        commitment=commitment,
        entities=extractor.extract("Julio"),
    )
    assert confirmed.state == OrderState.ORDER_CONFIRMED
    assert "Entrega: Delivery - San Isidro" in confirmed.response
    assert "Cliente: Julio" in confirmed.response


def test_checkout_v85_purchase_lock_quality_gate() -> None:
    engine = OrderFlowEngine()
    conv_id = "quality"
    engine.sync_from_commitment(conv_id, _commitment(size="M"))

    assert engine.is_catalog_forbidden(conv_id)
    assert engine.quality_score(conv_id, "Mira estas opciones para ti") == 0
    assert engine.quality_score(conv_id, "¿Cómo estás?") == 0
    assert engine.quality_score(conv_id, "Está saliendo muchísimo esta semana") == 0
    assert engine.quality_score(conv_id, "Continuemos con la entrega. ¿Delivery o tienda?") == 100


def test_checkout_v85_positive_intent_never_becomes_casual() -> None:
    engine = OrderFlowEngine()
    extractor = EntityExtractor()
    conv_id = "positive-intent"

    for phrase in ["si", "sí", "ok", "dale", "perfecto", "correcto", "lo quiero", "me lo llevo"]:
        engine.clear(conv_id)
        result = engine.process(
            conversation_id=conv_id,
            user_message=phrase,
            commitment=_commitment(size="M"),
            entities=extractor.extract(phrase),
        )
        assert result.handled
        assert result.state == OrderState.RESERVATION_PENDING
        assert "Te reservo" in result.response
        assert "Cómo estás" not in result.response
