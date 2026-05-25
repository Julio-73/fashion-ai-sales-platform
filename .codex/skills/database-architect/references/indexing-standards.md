# Indexing Standards

## Core Index Rule

Design indexes from query patterns, not guesswork. For every expected high-traffic query, identify:

- Tenant filter.
- Equality filters.
- Range filters.
- Sort order.
- Join columns.
- Pagination strategy.
- Selectivity.

## Tenant-Scoped Indexes

For tenant-owned tables, high-traffic indexes should usually begin with `empresa_id`.

Common patterns:

```sql
create index idx_clientes__empresa_id_created_at
on clientes (empresa_id, created_at desc);

create index idx_conversaciones__empresa_id_estado_updated_at
on conversaciones (empresa_id, estado, updated_at desc);

create index idx_mensajes__empresa_id_conversacion_id_created_at
on mensajes (empresa_id, conversacion_id, created_at desc);
```

## Foreign Key Indexes

- Index foreign keys used in joins, filters, cascades, or deletes.
- Composite indexes should include `empresa_id` when the child table is tenant-owned.
- Do not rely on primary key indexes to cover child-side foreign key lookups.

## Unique Indexes

Tenant-owned uniqueness must include `empresa_id`.

Examples:

```sql
create unique index uq_clientes__empresa_id_telefono
on clientes (empresa_id, telefono)
where deleted_at is null;

create unique index uq_whatsapp_mensajes__empresa_id_provider_message_id
on mensajes (empresa_id, provider, provider_message_id)
where provider_message_id is not null;
```

## Partial Indexes

Use partial indexes for hot subsets:

- active conversations
- unread messages
- pending jobs
- failed sync events
- non-deleted CRM records
- enabled AI agents

Example:

```sql
create index idx_conversaciones__empresa_id_abiertas
on conversaciones (empresa_id, updated_at desc)
where estado in ('abierta', 'pendiente');
```

## Analytics Indexes

Analytics/event tables should support:

- `(empresa_id, created_at desc)`
- `(empresa_id, nombre_evento, created_at desc)`
- `(empresa_id, entidad_tipo, entidad_id, created_at desc)`
- time-range scans, rollups, and retention jobs

Consider partitioning before over-indexing huge append-only tables.

## Index Review

Before adding an index, ask:

- Which query uses this?
- Does column order match equality, range, and sort behavior?
- Is it redundant with an existing index?
- Will it slow writes on high-volume tables?
- Does it preserve tenant safety?

