# Multi-Tenant Standards

## Mandatory empresa_id Rule

Every multi-tenant table MUST include `empresa_id`.

This includes:

- CRM tables.
- Customer tables.
- Lead and opportunity tables.
- Conversation and message tables.
- WhatsApp account/template/event tables.
- AI agent, prompt, automation, and interaction tables.
- Product catalog tables.
- Sales/order tables.
- Customer segmentation tables.
- Analytics and audit tables tied to tenant behavior.
- Tenant-owned join tables.

## Tenant-Safe Constraints

Every unique business rule inside tenant-owned data must include `empresa_id`.

Examples:

```sql
unique (empresa_id, telefono)
unique (empresa_id, email)
unique (empresa_id, provider, external_id)
unique (empresa_id, pipeline_id, nombre)
unique (empresa_id, sku)
```

Global uniqueness is allowed only for truly global tables or platform-level identities after careful design.

## Tenant-Safe Queries

Tenant-owned queries must filter by `empresa_id`.

Unsafe:

```sql
select * from clientes where id = $1;
```

Safe:

```sql
select * from clientes where empresa_id = $1 and id = $2;
```

Apply the same rule to updates, deletes, joins, analytics reads, exports, and background jobs.

## Tenant Context

- Pass tenant context explicitly through services and repositories.
- Never infer tenant from a mutable global.
- Validate that authenticated users have access to the requested `empresa_id`.
- Store `empresa_id` on idempotency records, jobs, outbox events, and provider webhook records when processing tenant-owned work.

## Row-Level Security

Consider PostgreSQL row-level security for sensitive tenant-owned tables:

- clientes
- conversaciones
- mensajes
- oportunidades
- ventas
- ai_interacciones
- eventos_analytics

RLS can strengthen isolation, but application queries must still include `empresa_id` for performance and clarity.

## Tenant Isolation Tests

Add tests that prove:

- A record from empresa A cannot be read through empresa B.
- Updates and deletes include `empresa_id`.
- Unique values can repeat across different empresas.
- Analytics queries are tenant-scoped.
- Background jobs do not process cross-tenant data accidentally.

