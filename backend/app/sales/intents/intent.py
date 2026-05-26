from __future__ import annotations

from enum import Enum


class IntentType(str, Enum):
    pricing_intent = "pricing_intent"
    purchase_intent = "purchase_intent"
    negotiation_intent = "negotiation_intent"
    shipping_intent = "shipping_intent"
    support_intent = "support_intent"
    product_interest = "product_interest"
    greeting = "greeting"
    unknown = "unknown"
