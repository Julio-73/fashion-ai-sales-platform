# Backend Standards

## FastAPI Structure

- Keep FastAPI routers thin: dependency resolution, request validation, authorization, service call, response mapping.
- Group routers by module and version: `presentation/routes.py` mounted through an API composition layer.
- Use Pydantic models for request and response schemas. Enable strict field types where practical.
- Use explicit dependency providers for database sessions, tenant context, authenticated user, services, repositories, settings, and provider clients.
- Standardize errors with typed exceptions and a central exception handler.

## Python Typing

- Use type hints on all public functions, methods, dependencies, services, repositories, adapters, and tests.
- Avoid untyped dict payloads. Use Pydantic models, dataclasses, TypedDict, or domain value objects.
- Keep `Any` as a last resort at vendor boundaries and immediately normalize into typed internal objects.
- Validate environment configuration with a typed settings object.

## Application Services

- Use command/query objects:

```python
class GenerateSalesReplyCommand(BaseModel):
    company_id: UUID
    conversation_id: UUID
    actor_user_id: UUID | None = None
    incoming_message_id: UUID
```

- Services should orchestrate one use case and delegate persistence to repositories and external calls to ports/adapters.
- Return typed DTOs or result models.
- Emit events for downstream analytics, notifications, CRM sync, and automation triggers.

## Integration Boundaries

- Wrap WhatsApp Business API, AI model providers, CRM APIs, and analytics exporters behind adapters.
- Normalize provider payloads into internal command/event models before processing.
- Verify webhook signatures before parsing business payloads.
- Store provider message IDs, delivery state, correlation IDs, retry counts, and raw payload references when needed for auditability.
- Never let provider-specific DTOs leak into domain services or frontend contracts.

## Background Work

- Move AI generation, WhatsApp delivery, CRM sync, analytics aggregation, imports, exports, and retries to background jobs when they can exceed request latency budgets.
- Jobs must be tenant-aware, idempotent, retry-safe, observable, and dead-letter capable.
- Use explicit idempotency keys for inbound webhooks and outbound message sends.

## Testing Standards

- Unit test domain policies and application services without FastAPI or the real database where practical.
- Add repository integration tests for tenant scoping, transactional behavior, indexes, and constraints.
- Add API tests for auth, authorization, validation failures, happy paths, and tenant isolation.
- Mock external providers at adapter boundaries, not deep inside business services.
- Include regression tests for multi-tenant data leakage risks.

## Production Readiness

- Use structured logs with request ID, company ID, user ID, job ID, provider, and correlation ID when available.
- Add metrics for API latency, job duration, queue depth, AI cost, token usage, WhatsApp delivery state, CRM sync failures, and webhook failures.
- Do not block request handlers on long AI or integration calls unless the use case explicitly requires synchronous behavior.

