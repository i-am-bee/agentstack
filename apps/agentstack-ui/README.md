# Agent Stack UI

## ENV

See [`.env.example`](./.env.example).

## Feature flags

Configure feature flags through the `FEATURE_FLAGS` environment variable. It expects a JSON object, for example:

```bash
FEATURE_FLAGS='{"LocalSetup":true,"Providers":true}'
```

All flags default to `false` when omitted.

- **LocalSetup** – Enables local development safeguards. When active, the run page requires a default LLM model to be configured and provider matching errors prompt developers to run `agentstack model setup`.
- **MCP** – Reserved for a future Model Context Protocol integration; leaving it `false` is recommended because the feature is not implemented yet.
- **ProviderBuilds** – Adds the option to import agents directly from a GitHub repository.
- **Providers** – Shows the “Agent providers” tab in Settings to manage providers.
- **Variables** – Shows the “Variables” tab in Settings to enable provider variable management.
