# Dependency Injection Standards

## Dependency Rules

- Use FastAPI dependencies for request-scoped resources.
- Keep dependency functions small and typed.
- Make services and repositories easy to override in tests.
- Avoid hidden global state for sessions, tenant context, users, settings, or clients.

## Core Dependencies

Provide standard dependencies for:

- `get_settings`
- `get_db_session`
- `get_current_user`
- `get_tenant_context`
- `require_permissions`
- module repositories
- module services
- provider clients

## Dependency Pattern

```python
async def get_cliente_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ClienteRepository:
    return ClienteRepository(session=session)

async def get_cliente_service(
    repository: ClienteRepository = Depends(get_cliente_repository),
) -> ClienteService:
    return ClienteService(repository=repository)
```

## Tenant Context

`TenantContext` should include:

- `empresa_id`
- authenticated user ID
- roles or permissions
- request/correlation ID when useful

Resolve and authorize tenant context before service and repository access.

## Test Overrides

Tests should override dependencies at the boundary:

- fake authenticated user
- fake tenant context
- test database session
- fake external provider client
- stub service for router-only tests

## Dependency Anti-Patterns

- Creating database sessions inside services manually.
- Instantiating provider SDKs inside route functions.
- Reading environment variables throughout business code.
- Using global mutable tenant or user context.
- Dependencies with large amounts of business logic.

