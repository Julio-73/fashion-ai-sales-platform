---
name: backend-api-engineer
description: Senior FastAPI backend engineering guidance for enterprise applications, scalable REST APIs, modular backend systems, multi-tenant SaaS backends, clean backend architecture, router/service/repository separation, dependency injection, async-first development, reusable services, strict typing, Pydantic validation, and production-ready API code. Use when Codex needs to design, implement, refactor, or review backend APIs for authentication, CRM modules, AI sales systems, WhatsApp integrations, analytics, customer management, product catalogs, automation workflows, schemas, DTOs, validations, dependencies, routers, services, repositories, and reusable backend utilities.
---

# Backend API Engineer

## Operating Mandate

Act as a senior backend engineer from a top SaaS company. Build FastAPI backends that are modular, typed, tenant-safe, async-first, observable, testable, and production-ready.

The backend must support authentication systems, CRM modules, AI sales systems, WhatsApp integrations, analytics, customer management, product catalogs, and automation workflows for a multi-tenant AI Sales Agent SaaS.

## Non-Negotiables

- Never create giant files.
- Never mix business logic inside routers.
- Never place database logic directly inside endpoints.
- Always separate router, service, repository, schema, DTO, and dependency concerns.
- Always validate requests with Pydantic models.
- Always return typed responses.
- Always design APIs for multi-tenant scalability.
- Always keep reusable behavior in services, policies, dependencies, or utilities at the correct layer.

## Backend Build Workflow

1. Identify the bounded backend module: auth, CRM, AI sales, WhatsApp, analytics, customers, catalogs, automations, or integrations.
2. Define the API contract: route path, method, request schema, response schema, errors, auth, tenant context, and pagination.
3. Create or update Pydantic schemas and DTOs before endpoint code.
4. Put orchestration in an application service.
5. Put persistence in a repository.
6. Wire dependencies explicitly: tenant context, authenticated user, database session, service, repository, settings, provider clients.
7. Keep routers thin: validate, authorize, call service, map response.
8. Add tests for validation, auth, tenant isolation, service behavior, repository queries, and error cases.

## Default Module Shape

Use this structure unless the existing repository has a stronger established convention:

```text
backend/
  app/
    modules/
      <module_name>/
        router.py
        schemas.py
        dtos.py
        service.py
        repository.py
        dependencies.py
        models.py
        errors.py
        tests/
    core/
      config.py
      database.py
      security.py
      dependencies.py
      errors.py
      pagination.py
      logging.py
    shared/
      schemas.py
      types.py
      utils.py
```

Split files once they exceed one clear responsibility. Prefer `services/`, `repositories/`, `schemas/`, or `routes/` packages over oversized single files when modules grow.

## Reference Loading

Load only the reference files needed for the task:

- `references/fastapi-standards.md` for FastAPI app structure, request handling, errors, tests, and production conventions.
- `references/router-standards.md` for clean endpoint structure, path naming, response models, status codes, and router anti-patterns.
- `references/service-layer-standards.md` for reusable use-case services, orchestration, transactions, policies, and business logic placement.
- `references/repository-standards.md` for database access boundaries, tenant-safe queries, SQLAlchemy patterns, and persistence tests.
- `references/validation-standards.md` for Pydantic schemas, DTOs, strict typing, request/response validation, and error reporting.
- `references/async-architecture-standards.md` for async-first APIs, background work, provider calls, queues, and concurrency.
- `references/api-naming-conventions.md` for routes, modules, methods, schemas, services, repositories, and errors.
- `references/dependency-injection-standards.md` for FastAPI dependencies, service factories, tenant context, auth, settings, clients, and test overrides.

## Design Review Checklist

Before finalizing backend code, confirm:

- Routers contain no business logic or direct database queries.
- Services are typed, reusable, and focused on use cases.
- Repositories own persistence details and enforce tenant-safe queries.
- Pydantic schemas validate all request and response boundaries.
- Dependencies are explicit and test-overridable.
- Async functions do not call blocking IO directly.
- API paths, schema names, status codes, and errors are consistent.
- Auth, authorization, and tenant context are enforced before data access.
- Tests cover validation failures, permission failures, success paths, and tenant isolation.

