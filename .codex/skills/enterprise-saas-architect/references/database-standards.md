# Database Standards

## Multi-Tenant PostgreSQL Design

- Make tenant ownership explicit with `company_id` or an equivalent tenant key on tenant-owned tables.
- Enforce tenant isolation in repository methods, query services, indexes, constraints, and tests.
- Prefer shared-schema multi-tenancy for this SaaS unless enterprise requirements justify schema-per-tenant or database-per-tenant.
- Consider PostgreSQL row-level security for high-risk tenant-owned data, especially conversations, customers, CRM records, and analytics events.
- Never rely on frontend filtering for tenant isolation.

## Core Tenant-Owned Data

Expected tenant-owned domains include:

- companies and company settings
- users, memberships, roles, invitations
- customers, leads, opportunities, accounts
- conversations, messages, message delivery events
- products, catalogs, collections, sizing attributes
- AI agents, prompts, automations, recommendations
- WhatsApp accounts, templates, webhook events
- CRM integrations and sync state
- analytics events, reports, aggregates

## Keys And Constraints

- Use UUID or ULID primary keys unless the existing project standard differs.
- Use foreign keys for tenant-owned relationships where practical.
- Include unique constraints scoped to `company_id`, such as phone number, external customer ID, integration account, or CRM pipeline name.
- Store external provider IDs with provider name and company ID in unique constraints.
- Add check constraints for controlled numeric and enum-like values where useful.

## Indexing

- Index common tenant-scoped access patterns:
  - `(company_id, created_at)`
  - `(company_id, status)`
  - `(company_id, customer_id)`
  - `(company_id, external_provider, external_id)`
  - `(company_id, conversation_id, created_at)`
- Add partial indexes for active records, pending jobs, unread conversations, and failed syncs.
- Use JSONB only for flexible provider metadata or analytics payloads; add generated columns or expression indexes for frequently queried fields.

## Migrations

- Write migrations as deliberate product changes, not incidental ORM dumps.
- Include backfills, defaults, constraints, and indexes in a safe order for production data.
- Avoid destructive migrations without an explicit rollout plan.
- Make migrations tenant-safe and consider table size, locks, and zero-downtime deployment.

## Analytics Data

- Separate transactional tables from append-only analytics events and aggregates.
- Keep analytics events immutable where possible.
- Include company ID, actor/user ID, entity IDs, event name, source, timestamp, and correlation ID.
- Use rollups/materialized views or dedicated query models for dashboards instead of expensive live joins on hot transactional tables.

## Data Lifecycle

- Define retention for raw webhook payloads, message content, AI prompts/responses, audit logs, and analytics events.
- Account for consent, opt-outs, deletion requests, and export requirements.
- Encrypt or otherwise protect sensitive customer contact data and integration tokens.

