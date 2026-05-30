import pytest
import re
from uuid import uuid4
from unittest.mock import AsyncMock
from app.smart_sales.brain import SmartSalesBrain

pytestmark = pytest.mark.asyncio


def _build_scenarios():
    from tests.sales_conversation_scenarios import SCENARIOS
    return [(s.id, s.name, s.category, s) for s in SCENARIOS]


SCENARIO_IDS = _build_scenarios()

COMMON_FALLBACK = [
    "chompa", "polo", "casaca", "jean", "zapatilla", "sneaker",
    "cuéntame", "buscas", "ayudo", "ideal", "entiendo", "opciones",
    "acabado", "calidad", "material", "premium", "accesible",
    "comparar", "estilo", "tipo", "modelo", "producto", "disponible",
    "separo", "enviamos", "casa", "recoger", "listo", "buenísima",
    "talla", "color", "precio", "pedido", "comprar", "confirmar",
    "dirección", "pago", "tarjeta", "decisión",
]


@pytest.fixture
def brain():
    session = AsyncMock()
    session.execute = AsyncMock(return_value=AsyncMock())
    result = session.execute.return_value
    result.unique = lambda: result
    result.scalars = lambda: result
    result.all = lambda: []
    return SmartSalesBrain(session=session)


@pytest.mark.parametrize(
    "scenario_id,name,category,scenario",
    [pytest.param(sid, nm, cat, s, id=sid) for sid, nm, cat, s in SCENARIO_IDS],
)
async def test_scenario(scenario_id, name, category, scenario, brain):
    empresa_id = uuid4()
    conversation_id = uuid4()
    for i, msg in enumerate(scenario.messages):
        reply = await brain.generate_reply(
            empresa_id=empresa_id,
            user_message=msg,
            conversation_id=conversation_id,
        )
        assert reply, f"[{scenario_id}] turn {i}: empty reply for '{msg}'"

        if scenario.forbidden_patterns:
            for pat in scenario.forbidden_patterns:
                assert not _contains_pattern(reply, pat), (
                    f"[{scenario_id}] turn {i}: forbidden pattern '{pat}' "
                    f"found in reply: {reply[:200]}"
                )

    if scenario.expected_patterns:
        last_reply = await brain.generate_reply(
            empresa_id=empresa_id,
            user_message=scenario.messages[-1],
            conversation_id=conversation_id,
        )
        assert any(
            _contains_pattern(last_reply, pat) for pat in scenario.expected_patterns
        ), (
            f"[{scenario_id}] none of expected patterns {scenario.expected_patterns} "
            f"found in final reply: {last_reply[:200]}"
        )


def _contains_pattern(text: str, pattern: str) -> bool:
    escaped = re.escape(pattern).replace(r"\ ", r"\s+")
    return re.search(escaped, text, re.IGNORECASE | re.UNICODE) is not None
