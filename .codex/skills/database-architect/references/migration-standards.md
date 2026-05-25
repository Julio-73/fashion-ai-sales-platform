# Migration Standards

## Production-Safe Migrations

Design migrations for live SaaS data:

1. Add nullable columns or defaults safely.
2. Backfill in batches for large tables.
3. Add indexes concurrently when supported by the migration tool.
4. Add constraints as not valid when needed, validate after backfill.
5. Switch application reads/writes.
6. Remove old columns only after a confirmed rollout window.

## Adding empresa_id

When adding `empresa_id` to an existing tenant-owned table:

1. Add nullable `empresa_id`.
2. Backfill from a reliable parent relationship.
3. Add indexes including `empresa_id`.
4. Add foreign key constraint to `empresas(id)`.
5. Add `not null` only after validation.
6. Update repository queries and tests.
7. Add tenant-scoped unique constraints.

Do not add `empresa_id` with a fake default tenant.

## Constraints

- Prefer explicit check constraints for stable domain states.
- Add foreign keys for real relationships.
- Add tenant-scoped unique constraints.
- Validate constraints against existing data before enforcing.

## Rollback Discipline

- Know whether a migration is reversible.
- Avoid destructive changes in the same migration as application behavior changes.
- For risky changes, use expand-migrate-contract.
- Keep data backfills idempotent.

## Migration Review Checklist

- Does every new tenant-owned table include `empresa_id`?
- Are UUID primary keys used?
- Are foreign keys, indexes, and unique constraints named consistently?
- Are audit timestamps present?
- Is the migration safe for production data volume?
- Does the application deploy order work?
- Are tests updated for tenant isolation and query behavior?

