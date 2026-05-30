import re
from dataclasses import dataclass
from enum import Enum

from app.smart_sales.contextual_commitment.selected_product_tracker import CommitmentData
from app.smart_sales.entity_extractor import ExtractedEntities
from app.smart_sales.product_matcher import MatchedProduct


class PurchaseStage(str, Enum):
    exploring = "explorando"
    comparing = "comparando"
    interested = "interesado"
    decided = "decidido"
    ready_to_buy = "listo_para_comprar"


@dataclass(frozen=True)
class SalesHumanizationV6Result:
    handled: bool
    response: str = ""
    stage: PurchaseStage = PurchaseStage.exploring
    should_mark_reserved: bool = False
    should_lock_product: bool = False
    product_name: str | None = None
    product_id: str | None = None
    product_category: str | None = None


BUY_PATTERNS = (
    r"\b(res[eé]rvame|reservar|reserva|separar|apartar|ap[áa]rtame)\b",
    r"\b(lo compro|la compro|me lo llevo|me la llevo|confirmo|conf[ií]rmame|pedido)\b",
)
GRATITUDE_PATTERNS = (r"\b(gracias|muchas gracias|mil gracias|te agradezco)\b",)
FAREWELL_PATTERNS = (r"\b(chao|adi[oó]s|hasta luego|nos vemos|eso es todo|nada m[aá]s)\b",)
COMPARISON_PATTERNS = (r"\b(compar|versus| vs |cu[aá]l es mejor|diferencia)\b",)
CATALOG_RESET_PATTERNS = (
    "aquí tienes más productos",
    "mira estas opciones",
    "tenemos estas opciones",
    "catálogo completo",
    "lista de productos",
)


class SalesHumanizationV6:
    """Deterministic context policy for premium human sales conversations."""

    def detect_stage(self, message: str, commitment: CommitmentData | None = None) -> PurchaseStage:
        msg = self._normalize(message)
        if self._matches(msg, BUY_PATTERNS):
            return PurchaseStage.ready_to_buy
        if self._matches(msg, COMPARISON_PATTERNS):
            return PurchaseStage.comparing
        if commitment and commitment.reservation_confirmed:
            return PurchaseStage.ready_to_buy
        if commitment and commitment.is_confirmed():
            return PurchaseStage.decided
        if commitment and commitment.is_committed():
            return PurchaseStage.interested
        if any(k in msg for k in ("me gusta", "me interesa", "lo quiero", "quiero ese")):
            return PurchaseStage.interested
        return PurchaseStage.exploring

    def process(
        self,
        *,
        user_message: str,
        commitment: CommitmentData | None,
        entities: ExtractedEntities | None = None,
        matched_products: list[MatchedProduct] | None = None,
    ) -> SalesHumanizationV6Result:
        msg = self._normalize(user_message)
        stage = self.detect_stage(user_message, commitment)
        product = self._resolve_product(commitment, matched_products)

        if product and commitment and not commitment.selected_product:
            return SalesHumanizationV6Result(
                handled=False,
                stage=stage,
                should_lock_product=True,
                product_name=product.name,
                product_id=product.product_id,
                product_category=product.category,
            )

        active_product = commitment.selected_product if commitment else None
        if not active_product:
            return SalesHumanizationV6Result(handled=False, stage=stage)

        color = self._best_color(commitment, entities)
        size = self._best_size(commitment, entities)

        if self._matches(msg, BUY_PATTERNS):
            if not size:
                return SalesHumanizationV6Result(
                    handled=True,
                    stage=PurchaseStage.decided,
                    response=(
                        f"Perfecto 😊 Tengo ubicado el {active_product} para ti.\n\n"
                        "Para dejarlo reservado necesito confirmar la talla. "
                        "¿Lo quieres en S, M, L o XL?"
                    ),
                )
            return SalesHumanizationV6Result(
                handled=True,
                stage=PurchaseStage.ready_to_buy,
                should_mark_reserved=True,
                response=self._reservation_response(active_product, color, size),
            )

        if entities and entities.color:
            return SalesHumanizationV6Result(
                handled=True,
                stage=PurchaseStage.decided,
                response=(
                    f"Perfecto 😊 El {active_product} en color {entities.color} está disponible.\n"
                    f"{self._size_line(size)}"
                ).strip(),
            )

        if entities and entities.size:
            return SalesHumanizationV6Result(
                handled=True,
                stage=PurchaseStage.decided,
                response=(
                    f"Sí 😊 El {active_product} en talla {entities.size} está disponible.\n"
                    f"{self._color_line(color)}"
                    "¿Te lo reservo?"
                ).strip(),
            )

        if self._matches(msg, GRATITUDE_PATTERNS):
            if commitment and commitment.reservation_confirmed:
                return SalesHumanizationV6Result(
                    handled=True,
                    stage=PurchaseStage.ready_to_buy,
                    response=(
                        "Con gusto 😊\n\n"
                        f"Tu reserva del {active_product} sigue guardada.\n\n"
                        "Cuando quieras continuar con la compra aquí estaré para ayudarte."
                    ),
                )
            return SalesHumanizationV6Result(
                handled=True,
                stage=stage,
                response=(
                    "Con gusto 😊\n\n"
                    f"Sigo atento al {active_product}. "
                    "Cuando quieras avanzamos con talla, color o forma de pago."
                ),
            )

        if self._matches(msg, FAREWELL_PATTERNS):
            return SalesHumanizationV6Result(
                handled=True,
                stage=stage,
                response=(
                    "Perfecto 😊 Gracias por escribirnos.\n\n"
                    f"Dejo el contexto del {active_product} guardado para cuando quieras continuar."
                ),
            )

        if "combina" in msg or "outfit" in msg or "con qué" in msg or "con que" in msg:
            return SalesHumanizationV6Result(
                handled=True,
                stage=PurchaseStage.interested,
                response=self._styling_response(active_product, color),
            )

        return SalesHumanizationV6Result(handled=False, stage=stage)

    def quality_score(self, response: str, commitment: CommitmentData | None) -> int:
        normalized = self._normalize(response)
        if not response.strip():
            return 0
        if commitment and commitment.is_committed():
            if any(pattern in normalized for pattern in CATALOG_RESET_PATTERNS):
                return 0
            if commitment.selected_product and commitment.selected_product.lower() not in normalized:
                return 40
        if "estoy aquí para ayudarte" in normalized and commitment and commitment.is_confirmed():
            return 0
        return 100

    def _reservation_response(self, product: str, color: str | None, size: str) -> str:
        lines = [
            "Perfecto 😊 Ya quedó reservado para ti.",
            "",
            product,
        ]
        if color:
            lines.append(f"Color: {color}")
        lines.append(f"Talla: {size}")
        lines.extend([
            "",
            "Si deseas continuar con la compra puedo ayudarte con el envío o forma de pago.",
        ])
        return "\n".join(lines)

    def _styling_response(self, product: str, color: str | None) -> str:
        color_hint = f" en {color}" if color else ""
        return (
            f"Para el {product}{color_hint}, lo más limpio es combinarlo con jean recto "
            "o pantalón neutro y zapatillas blancas. Si quieres un look más premium, "
            "sumaría una casaca ligera o accesorio minimalista."
        )

    def _resolve_product(
        self,
        commitment: CommitmentData | None,
        matched_products: list[MatchedProduct] | None,
    ) -> MatchedProduct | None:
        if commitment and commitment.selected_product:
            return None
        if not matched_products:
            return None
        in_stock = [p for p in matched_products if p.has_stock]
        return in_stock[0] if in_stock else matched_products[0]

    def _best_color(self, commitment: CommitmentData | None, entities: ExtractedEntities | None) -> str | None:
        return (entities.color if entities and entities.color else None) or (
            commitment.selected_color if commitment else None
        )

    def _best_size(self, commitment: CommitmentData | None, entities: ExtractedEntities | None) -> str | None:
        return (entities.size if entities and entities.size else None) or (
            commitment.selected_size if commitment else None
        )

    def _size_line(self, size: str | None) -> str:
        if size:
            return f"Talla {size} queda considerada. "
        return "¿Qué talla prefieres para revisarlo bien? "

    def _color_line(self, color: str | None) -> str:
        if color:
            return f"Color {color} queda considerado. "
        return ""

    def _matches(self, message: str, patterns: tuple[str, ...]) -> bool:
        return any(re.search(pattern, message, re.IGNORECASE) for pattern in patterns)

    def _normalize(self, text: str) -> str:
        return re.sub(r"\s+", " ", text.lower()).strip()
