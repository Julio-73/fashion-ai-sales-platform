# PostgreSQL Architecture Rules

## Table Classification

Classify every table before designing columns:

- Tenant-owned business table: must include `empresa_id`.
- Tenant-owned join table: must include `empresa_id`.
- Global reference table: no tenant ownership, rarely changes, shared by all tenants.
- Operational infrastructure table: queues, locks, outbox, jobs, idempotency, provider events.
- Analytics table: append-heavy events, snapshots, aggregates, reporting models.
- Audit table: append-only record of security or business-critical actions.

When in doubt, treat the table as tenant-owned and include `empresa_id`.

## Primary Keys

- Use UUID primary keys for all application tables.
- Name the primary key column `id`.
- Generate UUIDs using the project-standard PostgreSQL function or application layer.
- Do not use natural keys as primary keys for business entities.
- Keep external provider IDs in separate columns with scoped unique constraints.

Example:

```sql
id uuid primary key default gen_random_uuid()
```

## Audit Columns

Add these to business tables:

```sql
created_at timestamptz not null default now(),
updated_at timestamptz not null default now()
```

Use lifecycle columns when needed:

- `deleted_at` for soft deletion.
- `archived_at` for user-visible archive workflows.
- `activated_at` / `deactivated_at` for toggled configurations.
- `created_by_usuario_id` and `updated_by_usuario_id` for user-driven sensitive changes.

## Normalization

- Normalize transactional data to avoid duplicated customer, product, CRM, and conversation state.
- Use join tables for many-to-many relationships.
- Use lookup/reference tables when values require lifecycle, labels, localization, permissions, or tenant customization.
- Use enums/check constraints for small stable states only.
- Denormalize intentionally for analytics, immutable snapshots, search, or performance-critical read models.

## JSONB Usage

Use JSONB for:

- Provider metadata that varies by integration.
- Raw webhook payload references or bounded payload snapshots.
- Flexible analytics attributes.
- AI model diagnostics that are not core relational fields.

Do not use JSONB to hide structured business data such as customers, leads, product catalogs, sales stages, message state, or permissions.

## Anti-Patterns

- Tenant-owned tables without `empresa_id`.
- Tables without primary keys.
- Missing foreign keys for real relationships.
- Duplicating customer/product/conversation data across modules without snapshot semantics.
- Storing lists in comma-separated strings.
- Unbounded text status fields with no constraints.
- Generic tables like `data`, `records`, `items`, or `metadata` for core business entities.

