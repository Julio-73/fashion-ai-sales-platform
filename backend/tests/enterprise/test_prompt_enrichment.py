from uuid import UUID

import pytest

from app.ai.schemas.ai_schemas import (
    ConversationHistory,
    IntentType,
    ProductContextDetail,
    ProductInterest,
    RichContextData,
    RichCustomerProfile,
    SalesAction,
    SalesContextDetail,
)
from app.ai.services.llm_service import PromptComposer


class TestPromptEnrichment:
    def test_compose_with_rich_context(self):
        rich = RichContextData(
            customer=RichCustomerProfile(
                customer_id=UUID("00000000-0000-0000-0000-000000000001"),
                full_name="Cliente Premium",
                tags=["vip", "recurrente"],
                lead_score=85.0,
                lead_status="interested",
                priority="hot",
                total_conversations=12,
                average_order_value=250.0,
                customer_lifetime_value=3000.0,
                is_vip=True,
                preferred_colors=["negro", "rojo"],
                preferred_sizes=["M", "L"],
            ),
            conversation=ConversationHistory(
                total_messages=8,
                detected_intents=["purchase_intent", "pricing"],
                status="active",
            ),
            products=ProductContextDetail(
                preferred_styles=["elegante", "moderno"],
                upsell_candidates=[
                    ProductInterest(
                        product_name="Vestido Premium",
                        category="vestidos",
                        price=350.0,
                        has_stock=True,
                        stock_available=15,
                    )
                ],
                total_products_queried=5,
            ),
            sales=SalesContextDetail(
                conversion_probability="high",
                negotiation_stage="advanced",
                discount_sensitivity="low",
                buying_intent_trend="increasing",
                is_hot_lead=True,
                is_premium_customer=True,
                churn_risk="low",
            ),
        )

        result = PromptComposer.compose(
            intent=IntentType.purchase_intent,
            sales_action=SalesAction.suggest_upsell,
            customer_name="Cliente Premium",
            product_interests=["Vestido rojo"],
            conversation_history=["Hola, quiero un vestido", "Me gusta el rojo"],
            lead_score=85.0,
            conversation_stage="active",
            user_message="Quiero el vestido rojo",
            rich_context=rich,
        )

        assert "Cliente Premium" in result
        assert "VIP" in result or "vip" in result.lower()
        assert "negro" in result.lower() or "rojo" in result.lower()
        assert "vestido premium" in result.lower() or "Vestido Premium" in result
        assert "alta" in result.lower() or "high" in result.lower()
        assert "S/250" in result or "S/ 250" in result or "3000" in result

    def test_compose_without_rich_context_falls_back(self):
        result = PromptComposer.compose(
            intent=IntentType.pricing,
            sales_action=SalesAction.no_action,
            customer_name="Test",
            product_interests=[],
            conversation_history=[],
            lead_score=0.0,
            conversation_stage="new",
            user_message="Cuánto cuesta?",
        )

        assert "Test" in result
        assert "Cuánto cuesta" in result
        assert "Productos premium disponibles" in result or "No especificado" in result
        assert "Sin compras previas" in result

    def test_placeholder_values_replaced(self):
        rich = RichContextData(
            customer=RichCustomerProfile(
                customer_id=UUID("00000000-0000-0000-0000-000000000001"),
                full_name="Maria",
                tags=[],
                lead_score=45.0,
                lead_status="negotiating",
                priority="warm",
                total_conversations=3,
                is_vip=False,
            ),
            conversation=ConversationHistory(total_messages=0),
            products=ProductContextDetail(),
            sales=SalesContextDetail(discount_sensitivity="high"),
        )

        result = PromptComposer.compose(
            intent=IntentType.negotiation,
            sales_action=SalesAction.suggest_discount,
            customer_name="Maria",
            product_interests=["Zapatos"],
            conversation_history=[],
            lead_score=45.0,
            conversation_stage="negotiation",
            user_message="Me puedes hacer descuento?",
            rich_context=rich,
        )

        assert "15-20%" in result or "descuento" in result.lower()
        assert "Maria" in result

    def test_vip_context_appears_in_prompt(self):
        rich = RichContextData(
            customer=RichCustomerProfile(
                customer_id=UUID("00000000-0000-0000-0000-000000000001"),
                full_name="VIP Client",
                tags=["vip", "premium"],
                lead_score=95.0,
                is_vip=True,
                preferred_colors=["negro"],
                preferred_sizes=["M"],
            ),
            conversation=ConversationHistory(total_messages=10),
            products=ProductContextDetail(),
            sales=SalesContextDetail(),
        )

        result = PromptComposer.compose(
            intent=IntentType.pricing,
            sales_action=SalesAction.no_action,
            customer_name="VIP Client",
            product_interests=[],
            conversation_history=[],
            lead_score=95.0,
            conversation_stage="active",
            user_message="Qué tienes?",
            rich_context=rich,
        )

        assert "VIP" in result
        assert "negro" in result.lower()
