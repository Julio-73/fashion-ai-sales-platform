from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.smart_sales.brain import SmartSalesBrain
from app.smart_sales.product_matcher import MatchedProduct, MatchedVariant

pytestmark = pytest.mark.asyncio


def _product() -> MatchedProduct:
    return MatchedProduct(
        product_id="prod-polo-premium-black",
        name="Polo Premium Black",
        category="Polos",
        base_price=149,
        score=98,
        match_reason="exact",
        available_variants=[
            MatchedVariant(
                variant_id="var-polo-m",
                talla="M",
                color="Azul",
                price=149,
                stock=10,
                reserved_stock=0,
                sku="PPB-AZ-M",
            )
        ],
    )


async def test_order_flow_v85_e2e_product_size_delivery_address_name(monkeypatch) -> None:
    session = AsyncMock()
    brain = SmartSalesBrain(session=session)
    empresa_id = uuid4()
    conversation_id = uuid4()

    async def fake_find_products(*, empresa_id, entities, limit=15):
        return [_product()]

    monkeypatch.setattr(brain._product_context, "find_products", fake_find_products)

    first = await brain.generate_reply(
        empresa_id=empresa_id,
        conversation_id=conversation_id,
        user_message="Polo Premium Black talla M",
    )
    assert "Polo Premium Black" in first

    second = await brain.generate_reply(
        empresa_id=empresa_id,
        conversation_id=conversation_id,
        user_message="si",
    )
    assert "Te reservo" in second
    assert "Polo Premium Black" in second
    assert "Talla M" in second
    assert "Delivery" in second
    assert "Recojo en tienda" in second
    assert "cómo estás" not in second.lower()
    assert "recomiendo" not in second.lower()

    third = await brain.generate_reply(
        empresa_id=empresa_id,
        conversation_id=conversation_id,
        user_message="delivery",
    )
    assert "dirección" in third.lower()
    assert "catálogo" not in third.lower()

    fourth = await brain.generate_reply(
        empresa_id=empresa_id,
        conversation_id=conversation_id,
        user_message="San Isidro",
    )
    assert "A nombre de quién" in fourth

    final = await brain.generate_reply(
        empresa_id=empresa_id,
        conversation_id=conversation_id,
        user_message="Julio",
    )
    assert "Pedido confirmado" in final
    assert "Producto: Polo Premium Black" in final
    assert "Talla: M" in final
    assert "Entrega: Delivery - San Isidro" in final
    assert "Cliente: Julio" in final
    assert "Tu pedido quedó registrado correctamente" in final
