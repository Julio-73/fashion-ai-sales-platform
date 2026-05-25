# UI Naming Conventions

## Files

- Use kebab-case filenames: `customer-table.tsx`, `conversation-thread.tsx`.
- Use `.tsx` for React components and `.ts` for hooks, services, schemas, and types.
- Use suffixes that reveal purpose:
  - `.types.ts`
  - `.schema.ts`
  - `.service.ts`
  - `.hooks.ts`

## Components

- Use PascalCase component names.
- Name components by product purpose:
  - `CustomerTable`
  - `ConversationThread`
  - `AutomationRunList`
  - `CatalogProductCard`
  - `AnalyticsKpiGrid`

Avoid vague names like `Box`, `Panel`, `Section`, or `CardItem` unless they are true primitives.

## Hooks

- Prefix hooks with `use`.
- Name hooks by behavior:
  - `useCustomerFilters`
  - `useConversationSelection`
  - `useAutomationRuns`

## Services

Name typed API modules by domain:

```text
customers-api.ts
conversations-api.ts
analytics-api.ts
catalogs-api.ts
automations-api.ts
```

## Design Tokens

- Use semantic token names where possible: `background`, `foreground`, `muted`, `border`, `primary`, `destructive`.
- Avoid encoding one-off colors directly in product components.
- Keep variants named by intent: `default`, `secondary`, `outline`, `ghost`, `destructive`.

