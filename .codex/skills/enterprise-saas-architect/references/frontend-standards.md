# Frontend Standards

## Next.js Enterprise Structure

- Organize by product modules, not by generic technical buckets only.
- Keep route files focused on routing, data loading, layout composition, and permission gating.
- Put reusable domain UI, hooks, schemas, actions, and types inside `src/modules/<module>`.
- Keep shared primitives in `src/components/ui` and layout in `src/components/layout`.

Preferred shape:

```text
src/
  app/
    (dashboard)/
      conversations/
      crm/
      analytics/
      settings/
  modules/
    conversations/
      components/
      hooks/
      schemas/
      services/
      types/
    crm/
    ai-sales/
    analytics/
  lib/
    api/
    auth/
    validation/
    telemetry/
```

## Type Safety

- Type API requests and responses end to end.
- Use schema validation for forms, search params, server actions, and API responses.
- Avoid `any`, untyped JSON assumptions, and implicit stringly typed status values.
- Prefer generated API types when an OpenAPI contract exists.

## UI Boundaries

- Keep business decisions out of visual components.
- Use feature components for workflows such as lead assignment, AI reply approval, WhatsApp conversation triage, CRM pipeline updates, and analytics filters.
- Keep UI state local when it is purely visual; keep server state in a query/cache layer or framework-supported data flow.
- Keep permission checks centralized and visible at route/action boundaries.

## Data Access

- Use a typed API client layer instead of scattered `fetch` calls.
- Include tenant/company context through authenticated session or explicit route context; never hardcode company IDs.
- Handle loading, empty, error, optimistic, and permission-denied states for enterprise workflows.
- Do not expose backend secrets, provider credentials, or privileged integration tokens to the browser.

## Forms And Validation

- Validate forms client-side for usability and server-side for authority.
- Reuse schemas where possible without coupling browser bundles to server-only modules.
- Model fashion sales workflows explicitly: customer profile, sizing preferences, product interest, budget, channel, consent, conversation status, and opportunity stage.

## Frontend Anti-Patterns

- Giant page components with fetching, mutation, validation, table rendering, modal logic, and business branching in one file.
- Duplicate status mapping, validation rules, or formatting logic across screens.
- Client components by default when server components or server actions would reduce exposed complexity.
- Silent API failures or toast-only error handling for critical sales, CRM, billing, or integration workflows.

