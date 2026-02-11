---
trigger: always_on
---

# AgentStack UI Styling Guidelines

## SCSS Modules - MANDATORY

**CRITICAL**: When creating or modifying React components in `agentstack-ui`, you MUST use SCSS modules for styling. **NEVER use inline styles**.

### Rules

1. **Always create a corresponding `.module.scss` file** for each component that needs styling
2. **Import the SCSS module** as `classes` in the component
3. **Use CSS classes** instead of inline `style` props
4. **Use Sass variables** instead of CSS custom properties (e.g., `$spacing-05` not `var(--cds-spacing-05)`)
5. **Follow existing patterns** - look at similar components for reference

**Common Sass variables:**

- Spacing: `$spacing-01` through `$spacing-13`
- Colors: `$background`, `$text-primary`, `$text-secondary`, `$border-subtle`
- Typography: Use `@include type-style(body-01)` mixin
- Border radius: `$border-radius`
- Shadows: `$box-shadow`

### Example Pattern

**Component**: `MessageTextInput.tsx`

```tsx
import classes from "./MessageTextInput.module.scss";

export function MessageTextInput() {
  return (
    <form className={classes.root}>
      <div className={classes.form}>{/* content */}</div>
    </form>
  );
}
```

**SCSS Module**: `MessageTextInput.module.scss`

```scss
.root {
  margin-block-start: $spacing-05;
}

.form {
  display: flex;
  flex-direction: column;
  gap: $spacing-03;
}
```
