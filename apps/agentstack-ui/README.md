# Agent Stack UI

## ENV

See [`.env.example`](./.env.example).

## Feature flags

Configure feature flags through the `FEATURE_FLAGS` environment variable. It expects a JSON object, for example:

```bash
FEATURE_FLAGS='{
  "LocalSetup": true,
  "Providers": true
}'
```

All flags default to `false` when omitted.

- **Connectors** – Shows the “Connectors” tab in Settings and lets you list, connect, disconnect, and remove registered connectors.
- **LocalSetup** – Enables local development safeguards. When active, the run page requires a default LLM model to be configured and provider matching errors prompt developers to run `agentstack model setup`.
- **MCP** – Reserved for a future Model Context Protocol integration; leaving it `false` is recommended because the feature is not implemented yet.
- **ProviderBuilds** – Adds the option to import agents directly from a GitHub repository. *Requires `Providers` to also be enabled.*
- **Providers** – Shows the “Agent providers” tab in Settings and allows admin/developer users to manage agents, including adding agents using container image URLs and removing agents.
- **Variables** – Shows the “Variables” tab in Settings to enable provider variable management.

## Context token permissions override

Override the permissions used when the UI generates context tokens by supplying a `CONTEXT_TOKEN_PERMISSIONS` environment variable. Omit it to use the default grants (LLM + embeddings globally; files, vector stores, and context data within the current context). Example:

```bash
CONTEXT_TOKEN_PERMISSIONS='{
  "grant_global_permissions": {
    "llm": ["*"],
    "embeddings": ["*"]
  },
  "grant_context_permissions": {
    "files": ["*"],
    "vector_stores": ["*"],
    "context_data": ["*"]
  }
}'
```
