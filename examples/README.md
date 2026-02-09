# Examples

This directory contains example agents that serve three purposes:

1. **Standalone agents** — Each example is a fully functional agent that can be run independently for learning and experimentation.

2. **E2E tests** — Examples are used in end-to-end tests located in `apps/agentstack-server/tests/e2e/examples/`. This ensures all examples remain working and up-to-date.

3. **Documentation** — Examples are embedded directly into the [docs](../docs/) using [embedme](https://github.com/zakhenry/embedme) tags:
   ```mdx
   {/* <!-- embedme examples/agent-integration/multi-turn/basic-history/src/basic_history/agent.py --> */}
   ```
   This keeps documentation code samples in sync with actual tested examples.

## Creating a new example

Use the mise command to scaffold a new example and its e2e test from the templates in `.template/`.

```bash
mise run example:create <path> <description>
```

- `path` -- path relative to `examples/`, e.g. `agent-integration/multi-turn/basic-history`
- `description` -- short description of the example

The script automatically derives:

- **project name** from the last folder in the path (e.g. `basic-history`)
- **Python package name** by converting to snake_case (e.g. `basic_history`)
- **SDK relative path** from the directory depth

### Example

```bash
mise run example:create agent-integration/multi-turn/basic-history "Example demonstrating basic history."
```

This creates:

```
examples/agent-integration/multi-turn/basic-history/
  pyproject.toml
  src/basic_history/
    __init__.py
    agent.py

apps/agentstack-server/tests/e2e/examples/agent-integration/multi-turn/
  test_basic_history.py
```

It also adds a VS Code debug configuration to `examples/.vscode/launch.json`.

## Template placeholders

The template files in `.template/` use `%{...}` placeholders:

| Placeholder | Replaced with | Example |
|---|---|---|
| `%{EXAMPLE_NAME}` | Project name (kebab-case) | `basic-history` |
| `%{EXAMPLE_DESCRIPTION}` | Description | `Example demonstrating basic history.` |
| `%{EXAMPLE_NAME_SNAKE_CASE}` | Python package name | `basic_history` |
| `%{SDK_PATH}` | Relative path to SDK | `../../../../apps/agentstack-sdk-py` |

The directory `src/example_name/` and the function name `example_name` in `agent.py` are also renamed to the snake_case name.
