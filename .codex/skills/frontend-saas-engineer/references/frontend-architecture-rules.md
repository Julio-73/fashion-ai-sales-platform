# Frontend Architecture Rules

## Core Principles

- Organize by product module, not by generic technical buckets alone.
- Keep route files thin: route composition, metadata, permission gates, and high-level layout only.
- Put feature logic inside `src/modules/<module>`.
- Put reusable primitives in `src/components/ui` and reusable SaaS patterns in `src/components`.
- Keep data access behind typed service/API layers.
- Keep business workflow out of presentational components.

## Next.js App Router Standards

- Use route groups for dashboard, auth, marketing, and admin surfaces.
- Prefer server components for static or server-fetched composition.
- Use client components only for interactivity, browser APIs, form state, and live UI.
- Keep layouts stable and shared across related dashboard pages.
- Use loading and error boundaries where data can be slow or fail.

## Module Shape

```text
modules/<module>/
  components/
  hooks/
  schemas/
  services/
  types/
  utils/
```

Use subfolders when modules grow:

```text
modules/conversations/
  components/
    conversation-list.tsx
    conversation-thread.tsx
    message-composer.tsx
  hooks/
    use-conversation-filters.ts
  services/
    conversations-api.ts
  schemas/
    conversation.schema.ts
  types/
    conversation.types.ts
```

## Separation Rules

- Route/page: compose layout and fetch high-level data.
- Feature container: coordinate module state and data.
- Component: render a focused UI unit.
- Hook: encapsulate reusable client behavior.
- Service: call typed APIs.
- Schema: validate forms, filters, and API payloads.
- Type file: define shared contracts.

## Anti-Patterns

- Giant page files with fetching, tables, modals, forms, and business logic.
- Duplicate UI logic across CRM, customer, and catalog pages.
- One-off Tailwind styling when a reusable component variant should exist.
- Client components by default.
- Cross-module imports into internal component details.

