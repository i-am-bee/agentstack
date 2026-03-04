# Configuration Variables & Secrets Reference

Use this reference for mapping agent configuration variables and handling secrets safely.

Read the documentation first: [Environment Variables](https://agentstack.beeai.dev/stable/agent-integration/env-variables.md), [Manage Runtime Secrets](https://agentstack.beeai.dev/stable/agent-integration/secrets.md)

## Configuration Mapping Rule

It is critical to determine if the agent has any configuration and what environment variables it uses. You must investigate the following three sources:

1. **Agent code**: Look for `os.environ.get`, `os.getenv`, `os.environ[...]`, `dotenv`, or configuration classes.
2. **README.md**: Check deployment or configuration instructions.
3. **`.env` or `.env.example`** file if present in the repository.

If you identify variables, you must decide how to handle them. Use the following extension logic:

- **AgentStack Settings Extension**: Best for runtime configuration options that alter agent behavior (e.g., toggles, multiple-choice options like a "select" dropdown, "thinking mode").
- **AgentStack Env Variables Extension**: Best for low-level system/deployment configuration needed to run the service (e.g., `PORT`, `HOST`, database connection strings).
- **AgentStack Secrets Extension**: Best for sensitive user-level settings such as API keys and tokens for external services.

**API Tools & Environment Variables Constraint**: Third-party library integrations often implicitly depend on standard environment variables, which will fail in the AgentStack wrapper sandbox. You must systematically identify these required credentials, extract them using the `SecretsExtension`, and pass them explicitly as named parameters to component constructors.

**IMPORTANT CAUTION**: If you are unsure which extension to use for a particular secret or environment variable (especially regarding API keys to external services), **always ask the user** before making structural changes.

## Secret Handling Rule

**Do not use global environment assignment.** Never use `os.environ["KEY"] = secrets.data["KEY"]`. Instead, pass the secret value directly to the function or class that requires it (e.g., as a client constructor argument or a method parameter). This prevents global side effects and ensures that secrets are correctly scoped to the specific execution context.

## Requesting Secrets (Required)

Follow the official guide: [Manage Runtime Secrets](https://agentstack.beeai.dev/stable/agent-integration/secrets.md).

- Declare required secrets with the Secrets extension.
- Before using a secret, check whether it is present in secret fulfillments.
- If missing, request it through the Secrets extension and pause until provided.
- Do not proceed with external API/tool calls until the required secret is available.
- Never expose secret values in logs, messages, metadata, or trajectory output.

## Anti-Patterns (Required)

- **Never collect API keys or other sensitive secrets in an `initial_form`.**
- **Never pass secrets via non-sensitive form fields** (e.g., plain `TextField` in Forms) when Secrets or Env Variables extensions are appropriate.
- **Never log, print, persist, or echo secret values** in messages, metadata, errors, or trajectory output.

Sensitive values must be provided via:

- **Secrets extension** for user-level/runtime secrets.
- **Env Variables extension** for deployment-level configuration.
