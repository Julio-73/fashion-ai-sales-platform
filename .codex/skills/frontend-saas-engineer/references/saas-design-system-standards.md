# SaaS Design System Standards

## Visual Quality Bar

The UI must feel like a serious SaaS product:

- refined spacing
- consistent rhythm
- restrained color
- clear hierarchy
- polished controls
- purposeful density
- complete states
- accessible interactions

## TailwindCSS Rules

- Use Tailwind utility classes through reusable components and variants.
- Avoid scattered hardcoded one-off styling.
- Keep spacing and sizing consistent with the design system scale.
- Use `cn`/class composition helpers when available.
- Extract repeated class combinations into components or variants.

## shadcn/ui Rules

- Use shadcn/ui as the base for primitives.
- Compose primitives into product-specific SaaS components.
- Preserve accessibility behavior from primitives.
- Do not fork primitives unnecessarily.

## Spacing And Density

- Use compact enterprise spacing for operational dashboards.
- Keep page padding consistent.
- Keep card spacing tighter than landing pages.
- Align table, toolbar, and filter controls precisely.
- Avoid oversized hero typography inside dashboards.

## Color And Typography

- Use neutral surfaces with clear accent colors for action, status, and focus.
- Avoid one-note palettes and decorative gradients in operational UIs.
- Use status colors consistently for success, warning, error, neutral, and info.
- Keep typography readable, not theatrical.

## Interaction States

Every interactive element should have:

- hover state where appropriate
- focus-visible state
- disabled state
- loading state for async actions
- destructive confirmation when needed

## Feedback States

Build:

- skeleton loading states
- empty states with next action
- inline validation errors
- non-blocking toasts for lightweight feedback
- persistent error panels for critical failures
- permission-denied states for restricted features

