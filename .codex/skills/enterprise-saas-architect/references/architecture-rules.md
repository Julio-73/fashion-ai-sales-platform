# Architecture Rules

## Core Principles

- Design by bounded modules: company/account, identity, CRM, conversations, WhatsApp, AI sales automation, analytics, integrations, billing, notifications, and admin.
- Keep dependency direction inward: presentation -> application -> domain; infrastructure implements ports owned by application/domain.
- Put business rules in domain or application services, not framework handlers, React components, ORM entities, or vendor callbacks.
- Make every boundary typed: API schemas, service commands, repository return types, events, jobs, integration payloads, and configuration.
- Favor explicit composition over magic globals. Inject repositories, clients, clocks, tenant context, loggers, and unit-of-work boundaries.

## Layer Standards

### Presentation

- Accept HTTP/webhook/UI requests.
- Authenticate, authorize, validate, parse, and delegate.
- Return typed response DTOs.
- Do not contain orchestration, persistence queries, provider SDK calls, or business branching beyond request concerns.

### Application

- Own use cases such as qualifying a lead, syncing a WhatsApp message, creating a CRM opportunity, generating an AI reply, or producing analytics aggregates.
- Coordinate domain objects, repositories, integrations, transactions, and events.
- Enforce tenant-aware authorization rules before state changes.
- Return DTOs or result objects, not ORM entities.

### Domain

- Model durable business concepts: company, customer, lead, conversation, message, product, campaign, opportunity, sales agent, workflow, automation rule, and analytics event.
- Keep framework-free and persistence-free.
- Prefer value objects for money, phone numbers, locale, tenant IDs, message direction, channel, lifecycle status, and AI confidence.

### Infrastructure

- Implement repositories, database sessions, provider clients, queues, caches, telemetry exporters, and file/object storage.
- Keep vendor-specific behavior here: WhatsApp Business API, OpenAI/provider clients, CRM APIs, payment providers, email/SMS providers.
- Translate infrastructure errors into application-level errors.

## Modular Folder Standards

Prefer this backend module layout:

```text
modules/<module_name>/
  domain/
    entities.py
    value_objects.py
    policies.py
    events.py
  application/
    services.py
    commands.py
    queries.py
    ports.py
    dto.py
  infrastructure/
    repositories.py
    models.py
    adapters.py
  presentation/
    routes.py
    schemas.py
  tests/
```

Use separate files once a file exceeds one clear responsibility. Avoid catch-all `utils.py`, `helpers.py`, `common.py`, or `service.py` files that become junk drawers.

## Service Layer Pattern

- Name services by use case or cohesive capability: `LeadQualificationService`, `ConversationSyncService`, `AiReplyGenerationService`, `CrmPipelineService`.
- Accept typed command objects instead of loose dicts.
- Keep services stateless unless state is explicit and request-scoped.
- Make transactions explicit around write use cases.
- Keep idempotency keys for webhooks, payment events, WhatsApp messages, and AI job retries.

## Repository Pattern

- Define repository interfaces as application ports when services need persistence.
- Implement repositories in infrastructure using SQLAlchemy or the chosen ORM.
- Require tenant-scoped methods by default, such as `get_by_id(company_id, lead_id)`.
- Do not expose query builders, sessions, ORM models, or raw SQL outside repositories unless a specialized read model explicitly owns it.
- Use read repositories/query services for analytics and reporting instead of bloating transactional repositories.

## Anti-Pattern Blocklist

- Route handlers that perform database queries, AI calls, and branching business logic directly.
- One giant `models.py`, `schemas.py`, `routes.py`, `api.ts`, or `components.tsx`.
- Cross-module imports into another module's infrastructure internals.
- Shared global tenant state or tenant detection hidden in low-level database code only.
- Provider SDK calls scattered across services or UI code.
- Duplicate validation in multiple places without shared schemas or value objects.
- Synchronous long-running AI, CRM, or WhatsApp work inside request handlers.

