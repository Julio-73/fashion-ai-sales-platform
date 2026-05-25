"""Tests for Pydantic schema validation."""
from __future__ import annotations
import pytest
from pydantic import ValidationError
from app.modules.auth.schemas import RegisterRequest, LoginRequest, RefreshTokenRequest
from app.modules.customers.schemas import CustomerCreateRequest
from app.modules.products.schemas import ProductCreateRequest, ProductVariantCreateRequest
from app.modules.conversations.schemas import ConversationCreateRequest, MessageCreateRequest


class TestAuthSchemas:
    def test_valid_register(self):
        r = RegisterRequest(company_name="Mi Empresa", company_slug="mi-empresa", email="u@e.com", password="SecurePass123!")
        assert r.company_name == "Mi Empresa"

    def test_invalid_slug(self):
        with pytest.raises(ValidationError):
            RegisterRequest(company_name="T", company_slug="INVALID!!", email="u@e.com", password="SecurePass123!")

    def test_short_password(self):
        with pytest.raises(ValidationError):
            RegisterRequest(company_name="T", company_slug="t", email="u@e.com", password="Short1!")

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            LoginRequest(email="bad", password="password123")

    def test_short_refresh_token(self):
        with pytest.raises(ValidationError):
            RefreshTokenRequest(refresh_token="short")


class TestCustomerSchemas:
    def test_valid_create(self):
        assert CustomerCreateRequest(full_name="Juan", email="j@e.com").full_name == "Juan"

    def test_invalid_lead_status(self):
        with pytest.raises(ValidationError):
            CustomerCreateRequest(full_name="T", email="t@t.com", lead_status="invalid")

    def test_empty_tag(self):
        with pytest.raises(ValidationError):
            CustomerCreateRequest(full_name="T", email="t@t.com", tags=[""])

    def test_tag_too_long(self):
        with pytest.raises(ValidationError):
            CustomerCreateRequest(full_name="T", email="t@t.com", tags=["a" * 49])


class TestProductSchemas:
    def test_valid_create(self):
        r = ProductCreateRequest(name="Vestido Floral")
        assert r.status == "draft"

    def test_invalid_status(self):
        with pytest.raises(ValidationError):
            ProductCreateRequest(name="T", status="invalid")

    def test_negative_price(self):
        with pytest.raises(ValidationError):
            ProductCreateRequest(name="T", base_price=-10)

    def test_variant_sku(self):
        r = ProductVariantCreateRequest(sku="SKU-001", stock=5)
        assert r.sku == "SKU-001"


class TestConversationSchemas:
    def test_invalid_channel(self):
        with pytest.raises(ValidationError):
            ConversationCreateRequest(canal="telegram")

    def test_empty_message(self):
        with pytest.raises(ValidationError):
            MessageCreateRequest(role="agent", content="")

    def test_valid_message(self):
        r = MessageCreateRequest(role="agent", content="Hola", sender_name="Vendedor")
        assert r.role == "agent"
