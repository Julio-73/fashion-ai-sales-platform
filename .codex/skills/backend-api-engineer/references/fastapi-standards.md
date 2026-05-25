# FastAPI Standards

## Application Structure

- Compose the FastAPI app from module routers.
- Keep startup configuration, middleware, exception handlers, OpenAPI metadata, and router registration in a small application factory or main composition layer.
- Keep business modules independent enough to test without starting the whole app.
- Version public APIs with a clear prefix such as `/api/v1`.

## Endpoint Standards

- Use `response_model` for every route that returns a body.
- Use explicit status codes.
- Use typed path, query, header, and body parameters.
- Use dependencies for auth, tenant context, database sessions, services, pagination, and provider clients.
- Raise typed application exceptions and map them through central exception handlers.

## Production API Concerns

- Add request IDs and structured logs.
- Add consistent error payloads.
- Add rate limiting for auth, WhatsApp webhooks, AI endpoints, imports, exports, and automation triggers.
- Add pagination for list endpoints.
- Add idempotency for webhooks, message sends, automation executions, and payment-like operations.
- Never return ORM models directly.

## Testing

- Test routers with dependency overrides.
- Test service logic without FastAPI where practical.
- Test repository behavior against a real or representative database layer.
- Include auth, authorization, validation, tenant isolation, error mapping, and response shape tests.

## FastAPI Anti-Patterns

- Business rules inside route functions.
- SQLAlchemy queries inside endpoints.
- Untyped dict request bodies.
- Returning raw ORM objects.
- One monolithic `routes.py` for unrelated domains.
- Hidden global database sessions or tenant state.

