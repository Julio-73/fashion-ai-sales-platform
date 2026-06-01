import re
from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from app.smart_sales.contextual_commitment.selected_product_tracker import CommitmentData
from app.smart_sales.entity_extractor import ExtractedEntities


class OrderState(str, Enum):
    BROWSING = "browsing"
    PRODUCT_SELECTED = "product_selected"
    SIZE_SELECTED = "size_selected"
    PURCHASE_CONFIRMED = "purchase_confirmed"
    RESERVATION_PENDING = "reservation_pending"
    PAYMENT_PENDING = "payment_pending"
    DELIVERY_PENDING = "delivery_pending"
    ADDRESS_PENDING = "address_pending"
    CUSTOMER_NAME_PENDING = "customer_name_pending"
    CUSTOMER_INFO_PENDING = "customer_info_pending"
    ORDER_CONFIRMED = "order_confirmed"


@dataclass
class OrderContext:
    state: OrderState = OrderState.BROWSING
    product_name: str | None = None
    product_id: str | None = None
    product_category: str | None = None
    size: str | None = None
    color: str | None = None
    payment_method: str | None = None
    delivery_method: str | None = None
    delivery_address: str | None = None
    customer_name: str | None = None
    purchase_lock: bool = False
    persisted_order_id: UUID | None = None

    @property
    def has_active_purchase(self) -> bool:
        return self.purchase_lock and self.state != OrderState.ORDER_CONFIRMED


@dataclass(frozen=True)
class OrderFlowResult:
    handled: bool = False
    response: str = ""
    state: OrderState = OrderState.BROWSING


CONFIRMATION_PATTERNS = (
    r"\b(si|sí|ok|dale|correcto|perfecto|lo quiero|me interesa|res[eé]rvalo|res[eé]rvamelo|res[eé]rvame|comprar|me lo llevo|confirmo|listo|vamos)\b",
)
DELIVERY_PATTERNS = (r"\b(delivery|env[ií]amelo|env[ií]ame|env[ií]o|enviar|domicilio|a casa|casa)\b",)
PICKUP_PATTERNS = (r"\b(tienda|recojo|recoger|retiro|local)\b",)
PAYMENT_PATTERNS = (r"\b(al contado|efectivo|transferencia|yape|plin|tarjeta|pago|pagar)\b",)
RESET_PATTERNS = (
    "catálogo",
    "catalogo",
    "mira estas opciones",
    "te recomiendo",
    "más productos",
    "mas productos",
    "está saliendo muchísimo",
    "es una prenda premium",
    "estoy aquí para ayudarte",
)


class OrderFlowEngine:
    def __init__(self) -> None:
        self._contexts: dict[str, OrderContext] = {}

    def get_or_create(self, conversation_id: str) -> OrderContext:
        if conversation_id not in self._contexts:
            self._contexts[conversation_id] = OrderContext()
        return self._contexts[conversation_id]

    def sync_from_commitment(
        self,
        conversation_id: str,
        commitment: CommitmentData,
        entities: ExtractedEntities | None = None,
    ) -> OrderContext:
        ctx = self.get_or_create(conversation_id)
        if commitment.selected_product:
            ctx.product_name = commitment.selected_product
            ctx.product_id = commitment.selected_product_id
            ctx.product_category = commitment.selected_category
            if ctx.state == OrderState.BROWSING:
                ctx.state = OrderState.PRODUCT_SELECTED
        if commitment.selected_size:
            ctx.size = commitment.selected_size
        if commitment.selected_color:
            ctx.color = commitment.selected_color
        if entities:
            if entities.size:
                ctx.size = entities.size
            if entities.color:
                ctx.color = entities.color

        if ctx.product_name and ctx.size:
            ctx.purchase_lock = True
            if ctx.state in {OrderState.BROWSING, OrderState.PRODUCT_SELECTED, OrderState.SIZE_SELECTED}:
                ctx.state = OrderState.SIZE_SELECTED
        return ctx

    def set_product(
        self,
        conversation_id: str,
        *,
        product_name: str,
        product_id: str | None = None,
        product_category: str | None = None,
    ) -> OrderContext:
        ctx = self.get_or_create(conversation_id)
        ctx.product_name = product_name
        ctx.product_id = product_id
        ctx.product_category = product_category
        if ctx.state == OrderState.BROWSING:
            ctx.state = OrderState.PRODUCT_SELECTED
        return ctx

    def process(
        self,
        *,
        conversation_id: str,
        user_message: str,
        commitment: CommitmentData,
        entities: ExtractedEntities | None = None,
    ) -> OrderFlowResult:
        ctx = self.sync_from_commitment(conversation_id, commitment, entities)
        msg = self._normalize(user_message)

        if not ctx.product_name:
            return OrderFlowResult(state=ctx.state)

        if ctx.state == OrderState.ORDER_CONFIRMED:
            return self._handle_confirmed_order_message(ctx, msg)

        if ctx.product_name and not ctx.size and self._matches(msg, CONFIRMATION_PATTERNS):
            return OrderFlowResult(
                handled=True,
                state=ctx.state,
                response=f"Tengo seleccionado {ctx.product_name}.\n\nPara continuar necesito confirmar la talla.",
            )

        if ctx.product_name and ctx.size and ctx.state == OrderState.SIZE_SELECTED:
            if self._matches(msg, PAYMENT_PATTERNS):
                return self._handle_payment(ctx, msg)
            ctx.state = OrderState.RESERVATION_PENDING
            return OrderFlowResult(
                handled=True,
                state=ctx.state,
                response=self._reservation_response(ctx),
            )

        if ctx.has_active_purchase and self._matches(msg, PAYMENT_PATTERNS):
            return self._handle_payment(ctx, msg)

        if ctx.state in {OrderState.RESERVATION_PENDING, OrderState.PAYMENT_PENDING, OrderState.DELIVERY_PENDING}:
            if self._matches(msg, DELIVERY_PATTERNS):
                ctx.delivery_method = "Delivery"
                ctx.state = OrderState.ADDRESS_PENDING
                return OrderFlowResult(
                    handled=True,
                    state=ctx.state,
                    response=(
                        "Perfecto.\n\n"
                        "Realizaremos el envío.\n\n"
                        "¿A qué distrito o dirección deseas recibirlo?"
                    ),
                )
            if self._matches(msg, PICKUP_PATTERNS):
                ctx.delivery_method = "Recojo en tienda"
                ctx.state = OrderState.CUSTOMER_NAME_PENDING
                return OrderFlowResult(
                    handled=True,
                    state=ctx.state,
                    response="Perfecto.\n\n¿A nombre de quién dejamos la reserva?",
                )
            return OrderFlowResult(
                handled=True,
                state=ctx.state,
                response=(
                    "Continuemos con la entrega.\n\n"
                    "¿Cómo prefieres recibirlo?\n\n"
                    "1. Delivery\n"
                    "2. Recojo en tienda"
                ),
            )

        if ctx.state == OrderState.ADDRESS_PENDING:
            address = self._extract_address(user_message)
            if not address:
                return OrderFlowResult(
                    handled=True,
                    state=ctx.state,
                    response="Necesito el distrito o dirección para coordinar el envío.",
                )
            ctx.delivery_address = address
            ctx.state = OrderState.CUSTOMER_NAME_PENDING
            return OrderFlowResult(
                handled=True,
                state=ctx.state,
                response="Perfecto.\n\n¿A nombre de quién registramos el pedido?",
            )

        if ctx.state in {OrderState.CUSTOMER_NAME_PENDING, OrderState.CUSTOMER_INFO_PENDING}:
            name = self._extract_customer_name(user_message)
            if not name:
                return OrderFlowResult(
                    handled=True,
                    state=ctx.state,
                    response="¿A nombre de quién dejamos el pedido?",
                )
            ctx.customer_name = name
            ctx.state = OrderState.ORDER_CONFIRMED
            ctx.purchase_lock = False
            return OrderFlowResult(
                handled=True,
                state=ctx.state,
                response=self._confirmation_response(ctx),
            )

        return OrderFlowResult(state=ctx.state)

    def is_catalog_forbidden(self, conversation_id: str) -> bool:
        return self.get_or_create(conversation_id).has_active_purchase

    def quality_score(self, conversation_id: str, response: str) -> int:
        if not self.is_catalog_forbidden(conversation_id):
            return 100
        normalized = self._normalize(response)
        if any(pattern in normalized for pattern in RESET_PATTERNS):
            return 0
        if any(pattern in normalized for pattern in ("cómo estás", "como estas", "en qué puedo ayudarte")):
            return 0
        if not any(
            term in normalized
            for term in (
                "reserva",
                "pedido",
                "delivery",
                "recojo",
                "tienda",
                "nombre",
                "talla",
                "producto",
                "dirección",
                "direccion",
                "envío",
                "envio",
                "pago",
                "entrega",
                "distrito",
            )
        ):
            return 0
        return 100

    def clear(self, conversation_id: str) -> None:
        self._contexts.pop(conversation_id, None)

    def mark_persisted(self, conversation_id: str, order_id: UUID) -> None:
        self.get_or_create(conversation_id).persisted_order_id = order_id

    def _handle_payment(self, ctx: OrderContext, message: str) -> OrderFlowResult:
        ctx.payment_method = self._extract_payment_method(message)
        if not ctx.delivery_method:
            ctx.state = OrderState.DELIVERY_PENDING
            next_step = "Continuemos con la entrega."
        elif ctx.delivery_method == "Delivery" and not ctx.delivery_address:
            ctx.state = OrderState.ADDRESS_PENDING
            next_step = "Indícame el distrito o dirección para el envío."
        else:
            ctx.state = OrderState.CUSTOMER_NAME_PENDING
            next_step = "¿A nombre de quién dejamos el pedido?"
        return OrderFlowResult(
            handled=True,
            state=ctx.state,
            response=(
                "Perfecto.\n\n"
                "Método de pago registrado.\n\n"
                f"{next_step}"
            ),
        )

    def _reservation_response(self, ctx: OrderContext) -> str:
        return (
            "Perfecto.\n\n"
            "Te reservo:\n\n"
            f"* {ctx.product_name}\n"
            f"* Talla {ctx.size}\n\n"
            "¿Cómo prefieres recibirlo?\n\n"
            "1. Delivery\n"
            "2. Recojo en tienda"
        )

    def _confirmation_response(self, ctx: OrderContext) -> str:
        delivery = ctx.delivery_method or "Por confirmar"
        if ctx.delivery_address:
            delivery = f"{delivery} - {ctx.delivery_address}"
        return (
            "Pedido confirmado.\n\n"
            "Resumen:\n\n"
            f"Producto: {ctx.product_name}\n"
            f"Talla: {ctx.size}\n"
            f"Entrega: {delivery}\n"
            f"Cliente: {ctx.customer_name}\n\n"
            "Tu pedido quedó registrado correctamente."
        )

    def _handle_confirmed_order_message(self, ctx: OrderContext, message: str) -> OrderFlowResult:
        if re.search(r"\b(gracias|ok|dale|perfecto|listo|si|sí)\b", message, re.IGNORECASE):
            return OrderFlowResult(
                handled=True,
                state=ctx.state,
                response=(
                    "Con gusto.\n\n"
                    f"Tu pedido de {ctx.product_name} en talla {ctx.size} queda confirmado."
                ),
            )
        return OrderFlowResult(handled=True, state=ctx.state, response=self._confirmation_response(ctx))

    def _extract_customer_name(self, message: str) -> str | None:
        cleaned = re.sub(r"\b(a nombre de|soy|mi nombre es|para)\b", "", message, flags=re.IGNORECASE)
        cleaned = re.sub(r"[^A-Za-zÁÉÍÓÚáéíóúÑñ ]", "", cleaned).strip()
        words = [w.capitalize() for w in cleaned.split() if len(w) >= 2]
        if not words or len(words) > 4:
            return None
        return " ".join(words)

    def _extract_payment_method(self, message: str) -> str:
        msg = self._normalize(message)
        methods = {
            "al contado": "Al contado",
            "efectivo": "Efectivo",
            "transferencia": "Transferencia",
            "yape": "Yape",
            "plin": "Plin",
            "tarjeta": "Tarjeta",
        }
        for key, value in methods.items():
            if key in msg:
                return value
        return "Pago por confirmar"

    def _extract_address(self, message: str) -> str | None:
        cleaned = re.sub(
            r"\b(env[ií]ame|enviar|delivery|a casa|direccion|direcci[oó]n|distrito|en)\b",
            "",
            message,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" .,-")
        if len(cleaned) < 3:
            return None
        return cleaned.title()

    def _matches(self, message: str, patterns: tuple[str, ...]) -> bool:
        return any(re.search(pattern, message, re.IGNORECASE) for pattern in patterns)

    def _normalize(self, text: str) -> str:
        return re.sub(r"\s+", " ", text.lower()).strip()
