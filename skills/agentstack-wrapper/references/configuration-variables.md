# Configuration Variables & Secrets Reference

Use this reference for mapping agent configuration variables and handling secrets safely.

Read the documentation first: [Environment Variables](https://agentstack.beeai.dev/stable/agent-integration/env-variables.md), [Manage Runtime Secrets](https://agentstack.beeai.dev/stable/agent-integration/secrets.md)

## Configuration Mapping Rule

It is critical to determine if the agent has any configuration and what environment variables it uses. You must investigate the following three sources:

1. **Agent code**: Look for `os.environ.get`, `os.getenv`, `os.environ[...]`, `dotenv`, or configuration classes.
2. **README.md**: Check deployment or configuration instructions.
3. **`.env` or `.env.example`** file if present in the repository.

If you identify variables, you must decide how to handle them. Use the following extension logic without ambiguity:

- **Third-party API key/token required for a runtime call** (examples: Tavily, SerpAPI, Pinecone) → **Secrets extension (mandatory)**.
- **Deployment/runtime host settings** (examples: `HOST`, `PORT`, service URLs, database connection strings) → **Env Variables extension**.
- **User-tunable behavior options** (examples: mode/toggle/choice that changes behavior) → **Settings extension**.

If a third-party integration can truly run anonymously and the credential is optional, preserve optional behavior and do not force a secret demand.

**API Tools & Environment Variables Constraint**: Third-party library integrations often implicitly depend on standard environment variables, which will fail in the AgentStack wrapper sandbox. You must systematically identify these required credentials, extract them using the `SecretsExtension`, and pass them explicitly as named parameters to component constructors.

**IMPORTANT CAUTION**: If you are unsure which extension to use for a particular secret or environment variable (especially regarding API keys to external services), **always ask the user** before making structural changes.

## Secret Handling Rule

> [!CAUTION]
> **NEVER ASSIGN SECRETS TO `os.environ`!**
> Setting `os.environ["KEY"] = value` is a critical security vulnerability in AgentStack. The platform runs multiple isolated agent instances in a shared environment (multi-tenant infrastructure). Modifying the global OS environment exposes the private keys of one user to every other concurrent execution on the same pod.

Instead, pass the secret value directly to the function or class that requires it (e.g., as a client constructor argument: `Client(api_key=secret_value)`). This prevents global side effects and ensures that secrets are correctly scoped to the specific execution context.

## Requesting Secrets (Required)

Follow the official guide: [Manage Runtime Secrets](https://agentstack.beeai.dev/stable/agent-integration/secrets.md).

- Declare required secrets with the Secrets extension.
- Before using a secret, check whether it is present in `secret_fulfillments` and request it if missing:

  ```python
  api_key = None

  if secrets and secrets.data and secrets.data.secret_fulfillments and "API_KEY" in secrets.data.secret_fulfillments:
      api_key = secrets.data.secret_fulfillments["API_KEY"].secret
  else:
      secrets_meta = await secrets.request_secrets(
          params=SecretsServiceExtensionParams(secret_demands={"API_KEY": SecretDemand(name="API_KEY")})
      )
      if secrets_meta and secrets_meta.secret_fulfillments and "API_KEY" in secrets_meta.secret_fulfillments:
          api_key = secrets_meta.secret_fulfillments["API_KEY"].secret
  ```

- **Do not** assign values to `secrets.data` (e.g. `secrets.data["KEY"] = value`) since it is a Pydantic model (`SecretsServiceExtensionMetadata`), returning a `TypeError`. Save the secret to a local variable instead.
- **Do not** `yield` the result of `request_secrets` and do not `return` after calling it; it suspends execution automatically and returns the fulfillment when resumed.
- Do not proceed with external API/tool calls until the required secret is available.
- Never expose secret values in logs, messages, metadata, or trajectory output.

## Anti-Patterns (Required)

- **Never collect API keys or other sensitive secrets in an `initial_form`.**
- **Never pass secrets via non-sensitive form fields** (e.g., plain `TextField` in Forms) when Secrets or Env Variables extensions are appropriate.
- **Never log, print, persist, or echo secret values** in messages, metadata, errors, or trajectory output.

Sensitive values must be provided via:

- **Secrets extension** for user-level/runtime secrets.
- **Env Variables extension** for deployment-level configuration.

## External API Credential Audit (Required)

Before completion, explicitly confirm all three checks:

1. [ ] Every external API/tool client was inspected for credential source (implicit env lookup, constructor args, config object).
2. [ ] Any required credential was sourced from Secrets extension and passed explicitly to the client/tool constructor.
3. [ ] No wrapped execution path leaves required API credentials in implicit env-var mode (`os.getenv`, `os.environ`, `dotenv` lookups).
