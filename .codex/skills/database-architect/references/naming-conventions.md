# Naming Conventions

## Language And Style

- Use Spanish domain names consistently when the schema uses `empresa_id`.
- Use lowercase snake_case for tables, columns, indexes, constraints, migrations, and enum values.
- Use plural table names for entity collections: `clientes`, `productos`, `conversaciones`.
- Use singular foreign key column names: `cliente_id`, `producto_id`, `conversacion_id`, `empresa_id`.
- Do not mix `company_id` and `empresa_id` in the same schema.

## Required Column Names

- Primary key: `id`.
- Tenant key: `empresa_id`.
- Audit timestamps: `created_at`, `updated_at`.
- Soft delete: `deleted_at`.
- External provider ID: `<provider>_id` or `external_id` with `provider`.
- Status: `estado`.
- Type/category: `tipo`.

## Constraint Names

Use predictable names:

```text
pk_<table>
fk_<table>__<column>__<ref_table>
uq_<table>__<columns>
ck_<table>__<rule>
```

Examples:

```text
pk_clientes
fk_clientes__empresa_id__empresas
uq_clientes__empresa_id__telefono
ck_mensajes__direccion
```

## Index Names

Use:

```text
idx_<table>__<columns>
idx_<table>__<purpose>
```

Examples:

```text
idx_clientes__empresa_id_created_at
idx_conversaciones__empresa_id_estado_updated_at
idx_mensajes__empresa_id_conversacion_id_created_at
idx_eventos_analytics__empresa_id_nombre_created_at
```

## Join Tables

Name join tables by both sides, ordered by ownership or common product language:

```text
cliente_segmentos
producto_catalogos
usuario_roles
empresa_usuarios
```

Tenant-owned join tables must include `empresa_id`, even if both joined entities are tenant-owned.

## Migration Names

Name migrations by intent:

```text
create_clientes
add_empresa_id_to_mensajes
index_conversaciones_by_estado
backfill_cliente_segmentos_empresa_id
enforce_unique_whatsapp_message_provider_id
```

Avoid vague names such as `update_schema`, `fix_db`, or `new_tables`.

