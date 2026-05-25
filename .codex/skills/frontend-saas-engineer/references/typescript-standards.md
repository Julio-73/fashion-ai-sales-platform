# TypeScript Standards

## Strict Typing

- Use TypeScript for all frontend code.
- Type component props, API responses, form values, table rows, filters, and mutations.
- Avoid `any`; use `unknown` only at boundaries and narrow immediately.
- Prefer explicit domain types over loose records.
- Use discriminated unions for UI states and domain statuses.

## Props

```ts
type CustomerCardProps = {
  customer: CustomerSummary;
  onOpen: (customerId: string) => void;
  isSelected?: boolean;
};
```

- Keep prop names descriptive.
- Avoid passing entire API payloads when the component needs only a summary.
- Avoid boolean prop overload; use variants or composition.

## API Contracts

- Keep API client functions typed.
- Validate external or uncertain payloads with schemas.
- Use generated types when an OpenAPI contract exists.
- Keep frontend types aligned with backend DTOs, not database models.

## Forms

- Use schema-driven validation.
- Infer form types from schemas when practical.
- Keep server and client validation consistent.
- Avoid duplicating validation logic in components.

## Type Anti-Patterns

- `any` in component props.
- Stringly typed statuses repeated across files.
- Unchecked JSON response parsing.
- Types defined inside large components when reused elsewhere.
- Nullable fields used without intentional empty states.

