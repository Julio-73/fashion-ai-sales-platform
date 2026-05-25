# Relationship Standards

## Foreign Keys

- Use foreign keys for real relational ownership and references.
- Name foreign key columns with the referenced entity: `cliente_id`, `conversacion_id`, `producto_id`.
- Include `empresa_id` on tenant-owned child tables even when the parent also has `empresa_id`.
- Ensure repository queries match both `empresa_id` and entity IDs.

## Delete Behavior

Choose delete behavior intentionally:

- `restrict` for financial, CRM, sales, audit, and analytics-critical records.
- `cascade` only for true children with no independent business meaning.
- `set null` for optional references where historical records remain valid.
- Soft delete for user-facing records that need recovery or auditability.

Do not cascade-delete conversations, messages, sales, or audit records casually.

## Cardinality

Represent cardinality explicitly:

- One empresa has many usuarios through `empresa_usuarios`.
- One empresa has many clientes.
- One cliente can have many conversaciones.
- One conversacion has many mensajes.
- One cliente can have many oportunidades.
- One producto can belong to many catalogos through a join table.
- One segmento can include many clientes through `cliente_segmentos`.

## Join Tables

Join tables must have:

- UUID `id` primary key unless the project explicitly uses composite primary keys.
- `empresa_id` when tenant-owned.
- Foreign keys to both joined tables.
- Unique constraint across `empresa_id` and joined IDs.
- Audit timestamps when membership has product meaning.

Example:

```sql
create table cliente_segmentos (
  id uuid primary key default gen_random_uuid(),
  empresa_id uuid not null references empresas(id),
  cliente_id uuid not null references clientes(id),
  segmento_id uuid not null references segmentos_clientes(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint uq_cliente_segmentos__empresa_id_cliente_id_segmento_id
    unique (empresa_id, cliente_id, segmento_id)
);
```

## Relationship Anti-Patterns

- Polymorphic foreign keys without constraints for core business relationships.
- Duplicating parent attributes onto children instead of joining or snapshotting intentionally.
- Optional foreign keys where the domain requires ownership.
- Missing tenant key on child tables.
- Cross-tenant joins that match only by entity ID.

