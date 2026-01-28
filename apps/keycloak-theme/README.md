# Keycloak Custom Theme

Custom Keycloak theme for AgentStack platform built with [Keycloakify](https://keycloakify.dev).

## Development

### Storybook

All implemented pages are available in Storybook for development and testing:

```bash
mise run keycloak-theme:storybook
```

This will start Storybook on port 6006 where you can view and interact with all theme pages in isolation.

### Testing the theme locally

```bash
mise run keycloak-theme:run
```

This will start a local Keycloak instance with your theme loaded. See [Keycloakify documentation](https://docs.keycloakify.dev/testing-your-theme) for more details.

### Customizing the theme

See [Keycloakify CSS customization documentation](https://docs.keycloakify.dev/css-customization) for how to customize the theme.

## Building

```bash
mise run keycloak-theme:build
```
