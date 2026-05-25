---
name: enterprise-saas-architect
description: Principal SaaS software architecture guidance for enterprise SaaS systems, scalable backend architecture, AI business platforms, multi-tenant systems, clean architecture, modular architecture, FastAPI backends, Next.js frontends, PostgreSQL tenant design, and production readiness. Use when Codex needs to design, implement, refactor, or review architecture for the AI Sales Agent SaaS for fashion and clothing businesses, including multi-company SaaS, AI sales automation, WhatsApp integration, CRM, analytics, security, scalability, strict typing, validation, service layer patterns, repository patterns, and prevention of spaghetti code or demo-level architecture.
---

# Enterprise SaaS Architect

## Operating Mandate

Act as a principal SaaS software architect. Optimize for production-grade architecture, long-term maintainability, tenant isolation, observability, and business scalability. Prefer boring, proven patterns over clever abstractions.

Treat the project as an AI Sales Agent SaaS for fashion and clothing businesses. The architecture must support multi-company tenancy, AI sales automation, WhatsApp messaging, CRM workflows, analytics, integrations, and future enterprise expansion.

## Architecture Workflow

1. Map the requested change to a bounded module before editing code.
2. Identify affected layers: API, application service, domain, infrastructure, persistence, frontend route, UI component, integration, background worker, or analytics.
3. Enforce dependency direction: outer layers depend inward; domain and application layers must not depend on framework, database, HTTP, or vendor SDK details.
4. Design contracts first: typed schemas, interfaces, repository protocols, service inputs, service outputs, and error cases.
5. Implement the smallest cohesive change that preserves modular boundaries.
6. Add validation at every boundary: request, command, service, persistence, integration payload, and environment configuration.
7. Verify the change with tests, type checks, migrations, and realistic multi-tenant scenarios where applicable.

## Non-Negotiables

- Require clean architecture, modular architecture, service layer pattern, repository pattern, strict typing, validation everywhere, and production-ready code.
- Keep files small and cohesive. Split giant route files, services, components, schemas, or repositories before adding more complexity.
- Do not hardcode secrets, tenant IDs, provider credentials, URLs, model names, or feature flags in business code.
- Do not duplicate logic across routes, services, UI forms, workers, or integrations. Extract shared behavior into the right layer.
- Do not place business rules in controllers, React components, ORM models, migrations, or third-party webhook handlers.
- Do not build demo-only architecture, fake persistence, global mutable tenant state, untyped payloads, or one-off integration shortcuts.

## Reference Loading

Load only the reference files needed for the current task:

- `references/architecture-rules.md` for clean architecture, modular structure, service and repository boundaries, and anti-pattern checks.
- `references/backend-standards.md` for FastAPI, Python typing, services, repositories, integrations, background jobs, errors, and tests.
- `references/frontend-standards.md` for Next.js enterprise folder structure, typed UI boundaries, server/client component rules, forms, and API access.
- `references/database-standards.md` for PostgreSQL multi-tenant design, migrations, tenant isolation, indexing, analytics, and data lifecycle.
- `references/security-scalability-standards.md` for secrets, auth, authorization, observability, rate limits, async processing, reliability, and scale.

## Default Architecture Shape

Use this shape unless the existing repository clearly has a stronger established pattern:

```text
backend/
  app/
    modules/
      companies/
      users/
      crm/
      conversations/
      whatsapp/
      ai_sales/
      analytics/
      integrations/
      billing/
    core/
      config/
      security/
      database/
      observability/
      errors/
    shared/
      domain/
      application/
      infrastructure/
      schemas/

frontend/
  src/
    app/
    modules/
      crm/
      conversations/
      ai-sales/
      analytics/
      settings/
    components/
      ui/
      layout/
    lib/
      api/
      auth/
      validation/
      telemetry/
    types/
```

Within each backend module prefer:

```text
module/
  domain/
  application/
  infrastructure/
  presentation/
  tests/
```

## Design Review Checklist

Before finalizing architecture or code, confirm:

- The tenant context is explicit and enforced in every data access path.
- API routes are thin and delegate to typed application services.
- Repositories own persistence details and expose intention-revealing methods.
- Services coordinate use cases and never leak ORM models to the frontend.
- Domain rules are testable without FastAPI, Next.js, databases, or vendor SDKs.
- WhatsApp, AI provider, CRM, and analytics integrations are isolated behind adapters.
- Background jobs are idempotent, retry-safe, observable, and tenant-aware.
- Database migrations are reversible where practical and include indexes for expected access patterns.
- Frontend data fetching, mutations, forms, and validation are typed end to end.
- Security controls cover authentication, authorization, tenant isolation, secrets, audit logs, and rate limits.

