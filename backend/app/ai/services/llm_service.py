import logging
from pathlib import Path
from uuid import UUID

from app.ai.config import AISettings, get_ai_settings
from app.ai.providers.openai_provider import OpenAIProvider, OpenAIProviderError
from app.ai.schemas.ai_schemas import (
    ContextData,
    IntentClassification,
    IntentType,
    RichContextData,
    SalesAction,
)

logger = logging.getLogger("ai_sales_agent.ai.llm_service")

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"


class PromptComposer:
    _prompt_cache: dict[str, str] = {}

    @classmethod
    def _load_prompt(cls, filename: str) -> str:
        if filename not in cls._prompt_cache:
            path = PROMPTS_DIR / filename
            cls._prompt_cache[filename] = path.read_text(encoding="utf-8")
        return cls._prompt_cache[filename]

    @classmethod
    def compose(
        cls,
        *,
        intent: IntentType,
        sales_action: SalesAction,
        customer_name: str,
        product_interests: list[str],
        conversation_history: list[str],
        lead_score: float,
        conversation_stage: str,
        user_message: str,
        rich_context: RichContextData | None = None,
    ) -> str:
        system_prompt = cls._select_system_prompt(intent, sales_action)
        context_vars = cls._build_context_vars(
            customer_name=customer_name,
            product_interests=product_interests,
            conversation_history=conversation_history,
            lead_score=lead_score,
            conversation_stage=conversation_stage,
            rich_context=rich_context,
        )
        system_filled = system_prompt.format(**context_vars)
        return f"{system_filled}\n\nMensaje del cliente: {user_message}"

    @classmethod
    def _select_system_prompt(cls, intent: IntentType, sales_action: SalesAction) -> str:
        if sales_action == SalesAction.suggest_upsell:
            return cls._load_prompt("upsell_prompt.txt")
        if intent == IntentType.negotiation or sales_action == SalesAction.suggest_discount:
            return cls._load_prompt("negotiation_prompt.txt")
        if intent == IntentType.support:
            return cls._load_prompt("support_prompt.txt")
        if "_recovery" in str(sales_action) or str(intent) == "recovery":
            return cls._load_prompt("recovery_prompt.txt")
        return cls._load_prompt("system_sales_prompt.txt")

    @classmethod
    def _build_context_vars(
        cls,
        *,
        customer_name: str,
        product_interests: list[str],
        conversation_history: list[str],
        lead_score: float,
        conversation_stage: str,
        rich_context: RichContextData | None = None,
    ) -> dict[str, str]:
        interests_str = ", ".join(product_interests) if product_interests else "No especificado"

        purchase_history = "Sin compras previas"
        suggested_discount = "10%"
        suggested_products = "Productos premium disponibles"
        available_offers = "Ofertas disponibles en nueva colección"
        days_since_contact = "7"
        preferred_colors = "No especificado"
        preferred_sizes = "No especificado"
        preferred_styles = "No especificado"
        customer_vip_status = "No"
        customer_tags_str = ""
        negotiation_stage = "initial"
        conversion_prob = "unknown"
        churn_risk = "unknown"
        buying_trend = "stable"
        recent_messages_context = ""

        if rich_context:
            customer = rich_context.customer
            conversation = rich_context.conversation
            products = rich_context.products
            sales = rich_context.sales

            if customer.total_conversations > 0 or customer.average_order_value > 0:
                purchase_history_parts = []
                if customer.total_conversations > 0:
                    purchase_history_parts.append(f"{customer.total_conversations} conversaciones")
                if customer.average_order_value > 0:
                    purchase_history_parts.append(f"valor promedio: S/{customer.average_order_value:.2f}")
                if customer.customer_lifetime_value > 0:
                    purchase_history_parts.append(f"LTV: S/{customer.customer_lifetime_value:.2f}")
                purchase_history = ". ".join(purchase_history_parts) if purchase_history_parts else "Sin compras previas"

            if customer.is_vip:
                customer_vip_status = "Sí — Cliente VIP"
                suggested_products = "Colección premium y edición limitada"
                available_offers = "Acceso anticipado a nueva colección y descuentos exclusivos VIP"

            if customer.tags:
                customer_tags_str = ", ".join(customer.tags)

            if customer.preferred_colors:
                preferred_colors = ", ".join(customer.preferred_colors)
            if customer.preferred_sizes:
                preferred_sizes = ", ".join(customer.preferred_sizes)
            if products.preferred_styles:
                preferred_styles = ", ".join(products.preferred_styles)

            if products.upsell_candidates:
                upsell_names = [p.product_name for p in products.upsell_candidates[:3] if p.product_name]
                if upsell_names:
                    suggested_products = ", ".join(upsell_names)

            if sales.discount_sensitivity == "high":
                suggested_discount = "15-20%"
            elif sales.discount_sensitivity == "medium":
                suggested_discount = "10%"
            elif sales.discount_sensitivity == "low":
                suggested_discount = "5% (cliente de alto valor)"

            negotiation_stage = sales.negotiation_stage
            conversion_prob = sales.conversion_probability
            churn_risk = sales.churn_risk
            buying_trend = sales.buying_intent_trend

            if customer.last_interaction_at:
                from datetime import UTC, datetime
                last = customer.last_interaction_at
                if last.tzinfo is None:
                    last = last.replace(tzinfo=UTC)
                days_since = str((datetime.now(UTC) - last).days)
                days_since_contact = days_since

            if conversation.messages:
                recent_msgs = []
                for m in conversation.messages[:5]:
                    prefix = "Cliente:" if m.role in ("client", "user") else "Agente:"
                    recent_msgs.append(f"{prefix} {m.content[:150]}")
                recent_messages_context = "\n".join(recent_msgs)

        return {
            "customer_name": customer_name or "cliente",
            "product_interests": interests_str,
            "product_interest": interests_str,
            "conversation_history": " | ".join(conversation_history[-5:]) if conversation_history else "Sin historial",
            "lead_score": str(lead_score),
            "conversation_stage": conversation_stage,
            "suggested_discount": suggested_discount,
            "suggested_products": suggested_products,
            "purchase_history": purchase_history,
            "available_offers": available_offers,
            "days_since_contact": days_since_contact,
            "issue_description": "Consulta del cliente pendiente",
            "request_type": "soporte general",
            "preferred_colors": preferred_colors,
            "preferred_sizes": preferred_sizes,
            "preferred_styles": preferred_styles,
            "customer_vip_status": customer_vip_status,
            "customer_tags": customer_tags_str,
            "negotiation_stage": negotiation_stage,
            "conversion_probability": conversion_prob,
            "churn_risk": churn_risk,
            "buying_intent_trend": buying_trend,
            "recent_messages_context": recent_messages_context,
        }


class LLMService:
    def __init__(
        self,
        provider: OpenAIProvider | None = None,
        settings: AISettings | None = None,
    ) -> None:
        self._settings = settings or get_ai_settings()
        self._provider = provider or OpenAIProvider(settings=self._settings)
        self._fallback_response = self._settings.openai_fallback_response

    @property
    def is_configured(self) -> bool:
        return self._provider.is_configured

    async def generate_response(
        self,
        *,
        empresa_id: UUID,
        intent: IntentType,
        sales_action: SalesAction,
        context: ContextData | RichContextData,
        user_message: str,
        classification: IntentClassification | None = None,
    ) -> str:
        if not self._provider.is_configured:
            logger.info("OpenAI not configured, using fallback response for empresa=%s", empresa_id)
            return self._fallback_response

        rich_context = None
        if isinstance(context, RichContextData):
            rich_context = context

        try:
            prompt = PromptComposer.compose(
                intent=intent,
                sales_action=sales_action,
                customer_name=context.customer.customer_name if hasattr(context.customer, 'customer_name') else getattr(context.customer, 'full_name', ''),
                product_interests=context.product_interests if hasattr(context, 'product_interests') else [],
                conversation_history=context.recent_messages if hasattr(context, 'recent_messages') else [],
                lead_score=context.customer.lead_score if hasattr(context.customer, 'lead_score') else 0.0,
                conversation_stage=context.conversation_stage.value if hasattr(context, 'conversation_stage') else "active",
                user_message=user_message,
                rich_context=rich_context,
            )

            response = await self._provider.generate(
                system_prompt=prompt,
                user_message=user_message,
            )

            logger.info(
                "LLM response generated for empresa=%s, intent=%s, action=%s",
                empresa_id, intent.value, sales_action.value,
            )

            return response

        except OpenAIProviderError as exc:
            logger.error(
                "OpenAI provider error for empresa=%s, intent=%s: %s",
                empresa_id, intent.value, exc,
            )
            return self._fallback_response
        except Exception as _:
            logger.exception(
                "Unexpected LLM error for empresa=%s, intent=%s",
                empresa_id, intent.value,
            )
            return self._fallback_response
