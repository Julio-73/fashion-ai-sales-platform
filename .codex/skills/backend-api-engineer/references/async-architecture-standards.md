# Async Architecture Standards

## Async-First Rules

- Use async route handlers.
- Use async database sessions and async repository methods.
- Use async HTTP clients for provider calls.
- Do not call blocking IO directly inside async functions.
- Move long-running work to background jobs or queues.

## External Integrations

Wrap slow or failure-prone integrations behind async adapters:

- WhatsApp Business API.
- AI model providers.
- CRM APIs.
- Analytics exporters.
- Email/SMS providers.

Set timeouts, retries, and structured error handling at the adapter boundary.

## Background Work

Use background jobs for:

- AI reply generation.
- WhatsApp message delivery.
- CRM sync.
- Analytics aggregation.
- Imports and exports.
- Automation workflows.
- Webhook post-processing.

Jobs must be tenant-aware, idempotent, retry-safe, and observable.

## Concurrency Rules

- Bound concurrency for AI and provider calls.
- Avoid spawning unmanaged tasks inside request handlers.
- Use queues or task orchestration for durable work.
- Include correlation IDs across request, job, provider call, and database state.

## Async Anti-Patterns

- `requests` calls in async endpoints.
- CPU-heavy processing in the event loop.
- Waiting synchronously for long AI generations in ordinary CRUD endpoints.
- Fire-and-forget tasks with no retry, logging, or persistence.

