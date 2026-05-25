# Responsive Design Standards

## Layout Rules

- Design desktop, tablet, and mobile behavior intentionally.
- Use responsive grids, flex wrapping, min/max widths, and stable aspect ratios.
- Prevent text overlap, clipped buttons, and horizontal page overflow.
- Use horizontal scroll only for dense tables when a mobile card alternative is not better.
- Keep action bars reachable on mobile.

## Desktop

- Use dense but breathable layouts.
- Keep dashboards optimized for scanning.
- Use side panels for detail views when they improve workflow speed.
- Keep wide screens constrained enough that content remains readable.

## Tablet

- Collapse secondary sidebars.
- Convert multi-column dashboards to fewer columns.
- Preserve core actions without hiding them too deeply.

## Mobile

- Collapse sidebar into a sheet or bottom/nav pattern.
- Convert tables to cards or managed horizontal scroll.
- Prioritize search, filters, primary action, and active entity detail.
- Keep forms single-column.
- Make touch targets at least 40px tall.

## Accessibility

- Use semantic headings.
- Provide labels for controls and icon buttons.
- Ensure keyboard navigation and visible focus states.
- Maintain adequate contrast.
- Do not communicate status with color alone.
- Respect reduced-motion preferences for animations.

## Responsive Anti-Patterns

- Fixed widths that break on mobile.
- Long labels squeezed inside small buttons.
- Hidden primary actions on small screens.
- Cards nested inside cards.
- Layout shifts caused by loading, hover, or dynamic content.

