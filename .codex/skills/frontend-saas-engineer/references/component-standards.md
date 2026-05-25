# Component Standards

## Component Design

- Build components around product intent and reuse.
- Keep props typed, minimal, and explicit.
- Prefer composition over boolean prop explosions.
- Use shadcn/ui primitives as the base for buttons, dialogs, sheets, dropdowns, forms, tables, tabs, badges, cards, tooltips, and command palettes.
- Keep visual variants centralized with utilities such as `class-variance-authority` when available.

## Required SaaS Systems

Create reusable systems for:

- dashboard shell and sidebar
- data tables
- metric cards
- entity cards
- filters and search
- forms
- modals/dialogs/sheets
- loading skeletons
- empty states
- error states
- permission gates
- page headers and action bars

## Data Tables

Tables must support the workflow:

- search/filter controls
- sortable columns when useful
- pagination or infinite loading
- row actions
- selected/active row states
- loading skeleton
- empty state
- error state
- responsive overflow or mobile alternative

## Forms

Forms must include:

- typed schema validation
- clear labels and descriptions
- inline errors
- disabled/submitting state
- success/error feedback
- keyboard-accessible controls
- sensible default values

## Modals And Sheets

- Use dialogs for focused confirmation or small forms.
- Use sheets for contextual side workflows.
- Keep destructive actions explicit.
- Restore focus when closed.
- Avoid large multi-step workflows hidden in cramped modals.

## Component Anti-Patterns

- Components over 250-300 lines without a strong reason.
- Repeated card/table/form markup across modules.
- Hardcoded colors and spacing everywhere.
- Components that both fetch data and render low-level UI without separation.
- Missing loading, empty, and error states.

