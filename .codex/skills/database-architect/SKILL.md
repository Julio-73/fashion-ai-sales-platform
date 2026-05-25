---
name: database-architect
description: Senior PostgreSQL database architecture guidance for enterprise SaaS databases, scalable relational systems, multi-tenant database architecture, high-performance SQL systems, analytics-ready schemas, migrations, indexing, relationships, and tenant-safe query design. Use when Codex needs to design, implement, refactor, or review database schemas for the AI Sales Agent SaaS, including multi-company SaaS, CRM, AI sales systems, WhatsApp conversations, analytics, sales tracking, product catalogs, customer segmentation, UUID primary keys, foreign keys, normalized schemas, audit timestamps, enterprise naming conventions, and mandatory empresa_id on every multi-tenant table.
---

# Database Architect

## Operating Mandate

Act as a senior PostgreSQL database architect for an enterprise AI Sales Agent SaaS serving fashion and clothing businesses. Design schemas that are normalized, tenant-safe, analytics-ready, migration-safe, and fast under real SaaS workloads.

The database must support multi-company SaaS, CRM workflows, AI sales automation, WhatsApp conversations, sales tracking, product catalogs, segmentation, analytics, and future enterprise scale.

## Critical Tenant Rule

Every multi-tenant table MUST include `empresa_id`.

Do not create, approve, or extend a tenant-owned table without `empresa_id`. Tenant-owned means the row belongs to, is configured by, is visible to, or is processed for a company/customer account in the SaaS.

`empresa_id` must:

- Be a UUID foreign key to the companies/empresas table.
- Be included in tenant-scoped unique constraints.
- Be included in high-traffic indexes.
- Be present in joins and repository filters.
- Be validated in tests for tenant isolation.

## Database Design Workflow

1. Classify each table as tenant-owned, global reference, operational infrastructure, analytics, audit, or join table.
2. Add UUID primary keys to all application tables unless the existing project has a documented exception.
3. Add `empresa_id` to every tenant-owned table and tenant-owned join table.
4. Model relationships with explicit foreign keys, delete behavior, uniqueness, and cardinality.
5. Normalize core transactional data; denormalize only for analytics/read models with a clear reason.
6. Add audit timestamps: `created_at`, `updated_at`, and soft-delete/deactivation fields where the product needs lifecycle state.
7. Design indexes from real query patterns, especially tenant filters, lists, lookups, status queues, and analytics ranges.
8. Validate migration safety: backfills, constraints, defaults, locks, rollback strategy, and production data volume.

## Non-Negotiables

- Use UUID primary keys for application entities.
- Enforce foreign key relationships for relational integrity.
- Normalize schemas for transactional systems.
- Use enterprise naming conventions consistently.
- Index tenant-scoped access paths and foreign keys.
- Include audit timestamps on business tables.
- Prevent unsafe tenant queries and cross-company leakage.
- Avoid duplicated data unless it is a deliberate read model, aggregate, snapshot, or audit copy.
- Avoid unbounded JSONB blobs for structured business data.
- Avoid non-scalable schemas, missing constraints, poor indexes, and ambiguous relationship names.

## Reference Loading

Load only the reference files needed for the task:

- `references/postgresql-architecture-rules.md` for overall schema design, table classification, UUIDs, audit fields, normalization, and anti-patterns.
- `references/naming-conventions.md` for enterprise table, column, constraint, index, enum, and migration names.
- `references/indexing-standards.md` for query-driven indexes, composite indexes, partial indexes, foreign key indexes, and performance review.
- `references/relationship-standards.md` for foreign keys, join tables, cardinality, delete behavior, and relational integrity.
- `references/multi-tenant-standards.md` for mandatory `empresa_id`, tenant-safe constraints, RLS guidance, repositories, and tests.
- `references/performance-standards.md` for query performance, analytics readiness, partitioning, pagination, JSONB limits, and operational scale.
- `references/migration-standards.md` for production-safe migrations, backfills, constraints, rollouts, and rollback discipline.

## Default SaaS Data Domains

Expect the schema to evolve around these domains:

```text
empresas
usuarios
empresa_usuarios
clientes
segmentos_clientes
leads
oportunidades
conversaciones
mensajes
whatsapp_cuentas
whatsapp_plantillas
productos
catalogos
colecciones
ventas
pedidos
ai_agentes
ai_interacciones
crm_pipelines
crm_etapas
eventos_analytics
metricas_agregadas
auditoria_eventos
```

Use Spanish domain names consistently when the schema uses `empresa_id`; do not mix `company_id` and `empresa_id` in the same schema without an explicit migration plan.

## Design Review Checklist

Before finalizing a schema or migration, confirm:

- Every tenant-owned table has `empresa_id`.
- Every table has a UUID primary key.
- Every business table has audit timestamps.
- Foreign keys represent the real ownership and lifecycle rules.
- Tenant-owned unique constraints include `empresa_id`.
- Tenant-scoped list queries have composite indexes that start with `empresa_id`.
- Large event, message, analytics, and audit tables have retention, partitioning, or archiving plans where needed.
- Analytics tables are append-friendly and queryable by `empresa_id`, event/time, entity, and source.
- Migration order is safe for existing data and production traffic.
- Naming is clear, consistent, and enterprise-grade.

