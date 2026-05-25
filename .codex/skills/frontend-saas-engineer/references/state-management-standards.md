# State Management Standards

## State Categories

Classify state before choosing a tool:

- Server state: API data, caches, pagination, mutations.
- URL state: filters, tabs, search, sort, date ranges.
- Form state: field values, validation, submission.
- Local UI state: open modals, selected rows, active panels.
- Global app state: auth/session, company context, theme, feature flags.

## Server State

- Use the project's established data-fetching approach.
- Keep API calls in typed service functions.
- Handle loading, empty, error, refetching, and optimistic states.
- Invalidate or refresh affected queries after mutations.

## URL State

Use URL state for shareable dashboard controls:

- search
- filters
- sort
- pagination
- selected date range
- active tab when meaningful

## Form State

- Keep form state inside form components or form hooks.
- Use schema validation.
- Keep submit actions typed.
- Show field-level and form-level errors.

## Local UI State

- Keep local state near the UI that owns it.
- Extract hooks when behavior repeats.
- Do not use global state for ordinary modal toggles or hover details.

## State Anti-Patterns

- Storing server data manually in global state without a reason.
- Duplicating the same filter state in URL, component state, and store.
- Mutation logic scattered across UI components.
- Optimistic updates with no rollback path.
- Global stores that become dumping grounds.

