# Performance Standards

## Query Design

- Use cursor pagination for large tenant lists.
- Avoid unbounded `limit/offset` pagination on large tables.
- Select only needed columns on hot paths.
- Avoid N+1 query patterns in CRM, conversations, product catalogs, and analytics screens.
- Use query plans (`EXPLAIN ANALYZE`) for slow or complex queries.

## High-Volume Tables

Expect these tables to grow quickly:

- `mensajes`
- `conversaciones`
- `eventos_analytics`
- `ai_interacciones`
- `whatsapp_webhook_eventos`
- `auditoria_eventos`
- job/outbox tables

Plan indexes, retention, archiving, and partitioning before they become operational problems.

## Partitioning

Consider partitioning by time for append-heavy tables and by tenant only when tenant size distribution justifies it.

Good candidates:

- analytics events
- audit events
- WhatsApp webhook events
- AI interaction logs
- message delivery events

Partitioning must come with query patterns, retention jobs, and migration strategy.

## Analytics Readiness

- Keep immutable event tables append-friendly.
- Include `empresa_id`, event timestamp, event name, source, entity type, entity ID, and actor ID.
- Build aggregate tables or materialized views for dashboards instead of heavy live joins.
- Use snapshots for historical sales/product/customer state when later changes should not rewrite history.

## Product Catalog Performance

- Model product catalogs relationally for filters such as category, collection, size, color, price range, availability, gender/style, and SKU.
- Index tenant-scoped catalog browsing and product lookup queries.
- Avoid storing the entire catalog as one JSONB document.

## WhatsApp And CRM Performance

- Optimize conversation inbox queries by `empresa_id`, `estado`, `assigned_usuario_id`, unread count, and recent activity.
- Index message history by `empresa_id`, `conversacion_id`, and `created_at`.
- Index CRM pipeline views by `empresa_id`, stage/status, owner, value, and expected close date.

