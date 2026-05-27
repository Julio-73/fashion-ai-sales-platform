import logging
from pathlib import Path
from uuid import UUID

from app.ai.config import AISettings, get_ai_settings
from app.ai.providers.openai_provider import OpenAIProvider, OpenAIProviderError
from app.ai.schemas.ai_schemas import (
    ContextData,
    IntentClassification,
    IntentType,
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
    ) -> str:
        system_prompt = cls._select_system_prompt(intent, sales_action)
        context_vars = cls._build_context_vars(
            customer_name=customer_name,
            product_interests=product_interests,
            conversation_history=conversation_history,
            lead_score=lead_score,
            conversation_stage=conversation_stage,
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
    ) -> dict[str, str]:
        interests_str = ", ".join(product_interests) if product_interests else "No especificado"
        return {
            "customer_name": customer_name or "cliente",
            "product_interests": interests_str,
            "product_interest": interests_str,
            "conversation_history": " | ".join(conversation_history[-5:]) if conversation_history else "Sin historial",
            "lead_score": str(lead_score),
            "conversation_stage": conversation_stage,
            "suggested_discount": "10%",
            "suggested_products": "Productos premium disponibles",
            "purchase_history": "Sin compras previas",
            "available_offers": "Ofertas disponibles en nueva colección",
            "days_since_contact": "7",
            "issue_description": "Consulta del cliente pendiente",
            "request_type": "soporte general",
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
        context: ContextData,
        user_message: str,
        classification: IntentClassification | None = None,
    ) -> str:
        if not self._provider.is_configured:
            logger.info("OpenAI not configured, using fallback response for empresa=%s", empresa_id)
            return self._fallback_response

        try:
            prompt = PromptComposer.compose(
                intent=intent,
                sales_action=sales_action,
                customer_name=context.customer.customer_name,
                product_interests=context.product_interests,
                conversation_history=context.recent_messages,
                lead_score=context.customer.lead_score,
                conversation_stage=context.conversation_stage.value,
                user_message=user_message,
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
