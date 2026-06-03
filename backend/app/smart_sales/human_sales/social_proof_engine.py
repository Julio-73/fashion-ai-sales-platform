import logging
from collections import defaultdict

logger = logging.getLogger("smart_sales.human_sales.social_proof")


SOCIAL_PROOF_PHRASES: list[str] = [
    "Es uno de los más pedidos esta semana.",
    "Muchos clientes lo están solicitando.",
    "Está saliendo muchísimo estas semanas.",
    "Es de los favoritos de la temporada.",
    "Nuestros clientes lo recomiendan mucho.",
    "Está entre los más vendidos del mes.",
    "Lo están usando muchísimo.",
    "Es tendencia ahora mismo.",
    "Está siendo un éxito total.",
    "Todos los clientes que lo han probado quedan encantados.",
    "Es de los que más se repiten en pedidos.",
    "Es un bestseller de la colección.",
]

CATEGORY_PROOF: dict[str, list[str]] = defaultdict(
    lambda: SOCIAL_PROOF_PHRASES,
    {
        "polo": [
            "Es el polo más vendido de la colección.",
            "Nuestros clientes aman este polo.",
            "Está agotándose rápido esta temporada.",
        ],
        "camisa": [
            "Es una de las camisas más populares.",
            "Muchos clientes la eligen para eventos.",
        ],
        "pantalon": [
            "Es el pantalón favorito de la temporada.",
            "Nuestros clientes destacan su comodidad.",
        ],
        "vestido": [
            "Es uno de los vestidos más pedidos.",
            "Las clientas lo aman por su caída perfecta.",
        ],
        "zapatilla": [
            "Son las zapatillas más trendy del momento.",
            "Nuestros clientes las recomiendan por su comodidad.",
        ],
        "chaqueta": [
            "Es la chaqueta estrella de la colección.",
            "Está siendo un éxito esta temporada.",
        ],
    },
)

USED_PROOFS: dict[str, set[int]] = defaultdict(set)


class SocialProofEngine:
    def get_proof(self, product_category: str | None = None, conversation_id: str = "") -> str:
        if product_category:
            key = product_category.strip().lower()
            pool = CATEGORY_PROOF[key] if key in CATEGORY_PROOF else SOCIAL_PROOF_PHRASES
        else:
            pool = SOCIAL_PROOF_PHRASES

        used = USED_PROOFS[conversation_id]
        available = [i for i in range(len(pool)) if i not in used]

        if not available:
            available = list(range(len(pool)))
            used.clear()

        import random
        idx = random.choice(available)
        used.add(idx)

        return pool[idx]

    def reset(self, conversation_id: str) -> None:
        USED_PROOFS.pop(conversation_id, None)
