"""
Fixtures compartidos para todos los tests del backend.
Proporciona mocks de base de datos, tenant context y dependencias básicas.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.dependencies import AuthenticatedUser, TenantContext
from app.modules.auth.repository import AuthRepository
from app.modules.auth.service import AuthService
from app.modules.customers.repository import CustomerRepository
from app.modules.customers.service import CustomerService
from app.modules.products.repository import ProductRepository
from app.modules.products.service import ProductService
from app.modules.conversations.repository import ConversationRepository
from app.modules.conversations.service import ConversationService

# ──────────────────────────────────────────────
# UUIDs de prueba predecibles
# ──────────────────────────────────────────────

TEST_EMPRESA_ID = UUID("11111111-1111-4111-8111-111111111111")
TEST_USER_ID = UUID("22222222-2222-4222-8222-222222222222")
TEST_CUSTOMER_ID = UUID("33333333-3333-4333-8333-333333333333")
TEST_PRODUCT_ID = UUID("44444444-4444-4444-8444-444444444444")
TEST_VARIANT_ID = UUID("55555555-5555-4555-8555-555555555555")
TEST_IMAGE_ID = UUID("66666666-6666-4666-8666-666666666666")
TEST_CONVERSATION_ID = UUID("77777777-7777-4777-8777-777777777777")
TEST_FAMILY_ID = UUID("88888888-8888-4888-8888-888888888888")

# ──────────────────────────────────────────────
# Fixtures de mock de sesión de base de datos
# ──────────────────────────────────────────────


@pytest.fixture
def mock_session() -> AsyncMock:
    """Mock de AsyncSession de SQLAlchemy."""
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    session.add_all = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.execute = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    return session


# ──────────────────────────────────────────────
# Fixtures de contexto de tenant / usuario
# ──────────────────────────────────────────────


@pytest.fixture
def tenant_context() -> TenantContext:
    """TenantContext de prueba con permisos de owner."""
    return TenantContext(
        empresa_id=TEST_EMPRESA_ID,
        user_id=TEST_USER_ID,
        roles=["owner"],
        permissions={
            "auth:me",
            "customers:read",
            "customers:write",
            "products:read",
            "products:write",
            "chats:read",
            "chats:write",
            "conversations:read",
            "conversations:write",
            "analytics:read",
            "settings:manage",
            "users:manage",
        },
    )


@pytest.fixture
def authenticated_user() -> AuthenticatedUser:
    """AuthenticatedUser de prueba."""
    return AuthenticatedUser(
        user_id=TEST_USER_ID,
        empresa_id=TEST_EMPRESA_ID,
        roles=["owner"],
        permissions={
            "auth:me",
            "customers:read",
            "customers:write",
            "products:read",
            "products:write",
            "conversations:read",
            "conversations:write",
            "analytics:read",
            "settings:manage",
            "users:manage",
        },
    )


# ──────────────────────────────────────────────
# Fixtures de repositorios mockeados
# ──────────────────────────────────────────────


@pytest.fixture
def auth_repository(mock_session: AsyncMock) -> AuthRepository:
    """AuthRepository con session mockeada."""
    return AuthRepository(session=mock_session)


@pytest.fixture
def auth_service(auth_repository: AuthRepository) -> AuthService:
    """AuthService con repository mockeado."""
    return AuthService(repository=auth_repository)


@pytest.fixture
def customer_repository(mock_session: AsyncMock) -> CustomerRepository:
    """CustomerRepository con session mockeada."""
    return CustomerRepository(session=mock_session)


@pytest.fixture
def customer_service(customer_repository: CustomerRepository) -> CustomerService:
    """CustomerService con repository mockeado."""
    return CustomerService(repository=customer_repository)


@pytest.fixture
def product_repository(mock_session: AsyncMock) -> ProductRepository:
    """ProductRepository con session mockeada."""
    return ProductRepository(session=mock_session)


@pytest.fixture
def product_service(product_repository: ProductRepository) -> ProductService:
    """ProductService con repository mockeado."""
    return ProductService(repository=product_repository)


@pytest.fixture
def conversation_repository(mock_session: AsyncMock) -> ConversationRepository:
    """ConversationRepository con session mockeada."""
    return ConversationRepository(session=mock_session)


@pytest.fixture
def conversation_service(
    conversation_repository: ConversationRepository,
) -> ConversationService:
    """ConversationService con repository mockeado."""
    return ConversationService(repository=conversation_repository)


# ──────────────────────────────────────────────
# Helpers para crear objetos mock del ORM
# ──────────────────────────────────────────────


def create_mock_orm_model(
    model_class: type,
    /,
    **kwargs,
) -> MagicMock:
    """Crea un MagicMock que se comporta como una instancia de modelo SQLAlchemy."""
    instance = MagicMock(spec=model_class)
    for key, value in kwargs.items():
        setattr(instance, key, value)
    return instance
