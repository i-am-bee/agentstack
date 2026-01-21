# Keycloak Custom Theme

Custom Keycloak theme for AgentStack platform built with [Keycloakify](https://keycloakify.dev).

## Development

### Testing the theme locally

```bash
mise run keycloak-theme:run
```

This will start a local Keycloak instance with your theme loaded. See [Keycloakify documentation](https://docs.keycloakify.dev/testing-your-theme) for more details.

### Customizing the theme

See [Keycloakify CSS customization documentation](https://docs.keycloakify.dev/css-customization) for how to customize the theme.

## Building

### Prerequisites

You need to have [Maven](https://maven.apache.org/) installed to build the theme (Maven >= 3.1.1, Java >= 7).  
The `mvn` command must be in the $PATH.

-   On macOS: `brew install maven`
-   On Debian/Ubuntu: `sudo apt-get install maven`
-   On Windows: `choco install openjdk` and `choco install maven` (Or download from [here](https://maven.apache.org/download.cgi))

### Build JAR file

To build just the theme JAR file:

```bash
mise run keycloak-theme:build-jar
```

This generates the JAR file in `dist_keycloak/keycloak-theme-for-kc-all-other-versions.jar`.

### Build Docker image

To build a custom Keycloak Docker image with the theme built-in:

```bash
mise run keycloak-theme:build-docker
```

This creates a Docker image tagged as `ghcr.io/i-am-bee/agentstack/keycloak-theme:local`.

## Deployment

### Using custom Docker image (Recommended for Production)

To deploy Keycloak with the custom theme as a Docker image:

1. Build the Docker image:

    ```bash
    mise run keycloak-theme:build-docker
    ```

2. Deploy with Helm using the custom image:
    ```bash
    mise run agentstack:start -- \
      --set keycloak.customTheme.enabled=true \
      --set keycloak.customTheme.image.tag=local
    ```

For production, push the image to your registry and use the appropriate tag.

### Using ConfigMap (Development/Testing)

By default, theme files are mounted via Kubernetes ConfigMap. This is suitable for development but not recommended for production as ConfigMaps have size limitations.

To use this method:

```bash
mise run agentstack:start
```

The theme files from `helm/keycloak-theme/**` will be automatically mounted.

## Theme Configuration

In Helm values (`helm/values.yaml`):

```yaml
keycloak:
    customTheme:
        enabled: false # Set to true to use custom Docker image
        image:
            repository: ghcr.io/i-am-bee/agentstack/keycloak-theme
            tag: "" # Uses Chart.AppVersion by default
            pullPolicy: IfNotPresent
```

## Initializing additional themes

### Account theme

```bash
npx keycloakify initialize-account-theme
```

### Email theme

```bash
npx keycloakify initialize-email-theme
```

# GitHub Actions

The starter comes with a generic GitHub Actions workflow that builds the theme and publishes
the jars [as GitHub releases artifacts](https://github.com/keycloakify/keycloakify-starter/releases/tag/v10.0.0).  
To release a new version **just update the `package.json` version and push**.

To enable the workflow go to your fork of this repository on GitHub then navigate to:
`Settings` > `Actions` > `Workflow permissions`, select `Read and write permissions`.
