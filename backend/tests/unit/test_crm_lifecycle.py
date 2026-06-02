"""Unit tests for the CRM Customer 360 VIP engine classification."""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.modules.crm.service import classify_lifecycle_status


class TestClassifyLifecycleStatus:
    def test_vip_by_order_count(self):
        assert (
            classify_lifecycle_status(
                order_count=5,
                lifetime_value=Decimal("0"),
                days_since_last_purchase=2,
                customer_age_days=30,
            )
            == "vip"
        )

    def test_vip_by_lifetime_value(self):
        assert (
            classify_lifecycle_status(
                order_count=1,
                lifetime_value=Decimal("1500"),
                days_since_last_purchase=1,
                customer_age_days=20,
            )
            == "vip"
        )

    def test_recurrente_with_three_orders(self):
        assert (
            classify_lifecycle_status(
                order_count=3,
                lifetime_value=Decimal("500"),
                days_since_last_purchase=2,
                customer_age_days=90,
            )
            == "recurrente"
        )

    def test_activo_with_recent_purchase(self):
        assert (
            classify_lifecycle_status(
                order_count=2,
                lifetime_value=Decimal("250"),
                days_since_last_purchase=10,
                customer_age_days=120,
            )
            == "activo"
        )

    def test_nuevo_when_no_orders_and_recent(self):
        assert (
            classify_lifecycle_status(
                order_count=0,
                lifetime_value=Decimal("0"),
                days_since_last_purchase=None,
                customer_age_days=10,
            )
            == "nuevo"
        )

    def test_inactivo_when_no_orders_and_old(self):
        assert (
            classify_lifecycle_status(
                order_count=0,
                lifetime_value=Decimal("0"),
                days_since_last_purchase=None,
                customer_age_days=120,
            )
            == "inactivo"
        )

    def test_inactivo_when_old_purchase(self):
        assert (
            classify_lifecycle_status(
                order_count=2,
                lifetime_value=Decimal("200"),
                days_since_last_purchase=120,
                customer_age_days=400,
            )
            == "inactivo"
        )

    def test_vip_takes_priority_over_recurrente(self):
        # Even though 7 orders also makes it recurrente, VIP wins.
        assert (
            classify_lifecycle_status(
                order_count=7,
                lifetime_value=Decimal("2000"),
                days_since_last_purchase=5,
                customer_age_days=200,
            )
            == "vip"
        )
