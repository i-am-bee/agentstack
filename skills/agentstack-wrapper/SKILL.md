---
name: agentstack-wrapper
description: Wrap an existing Python agent as an Agent Stack service using agentstack-sdk server wrapper, without changing business logic.
metadata:
  internal: true
---

# AgentStack Wrapper Skill

## Purpose

Transform an existing Python agent into a running [AgentStack](https://agentstack.beeai.dev/stable/introduction/welcome.md) service. The wrapper exposes the agent via the A2A protocol so it can be discovered, called, and composed with other agents on the platform.

## When to Use

- You have a working Python agent (CLI tool, library function, framework-based agent) and need to deploy it as an AgentStack service.
- You want to expose an agent over A2A without rewriting its business logic.

## Prerequisites

- Python 3.12+
- The agent's source code is available locally
- `agentstack-sdk` version fetched at wrap time from PyPI and pinned in project dependencies using `~=`
- `a2a-sdk` only if the project manages it directly, and pin it to a version compatible with the selected `agentstack-sdk` (do not independently chase the latest `a2a-sdk` if resolver constraints differ)

## Constraints (must follow)

| ID  | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| C1  | **No business-logic changes.** Only modify code for AgentStack compatibility.                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| C2  | **Strict minimal changes.** Do not add auth, Dockerfile (containerization is optional and separate), telemetry, or platform middleware unless explicitly requested. If an agent works with simple text, don't force a Form. If it works with env vars, refactor minimally.                                                                                                                                                                                                                                                       |
| C3  | **Cleanup temp files.** If the agent downloads or creates helper files at runtime, add a cleanup step before the function returns.                                                                                                                                                                                                                                                                                                                                                                                               |
| C4  | **Prioritize Public Access (No redundant tokens).** Only use the Secrets extension if the secret is strictly mandatory for the agent's core functionality and no public/anonymous access is viable. Do not add secrets or tokens that increase configuration burden if they were optional in the original agent (e.g., optional GitHub token). Preserve existing optional auth behavior unless removal is explicitly approved and documented as a behavior change. API keys must be passed explicitly, never read from env vars. |
| C5  | **Detect existing tooling.** If the project uses `requirements.txt`, add `agentstack-sdk~=<VERSION>` there. If it uses `pyproject.toml`, add it there. Add `a2a-sdk` only when the project manages it directly, and keep it compatible with the chosen `agentstack-sdk` version. Never force `uv` or create duplicate manifests.                                                                                                                                                                                                 |
| C6  | **Import Truth and Validation.** All imports must match modules that exist in the active virtual environment (`agentstack_sdk`, `a2a`). If official docs conflict with installed package layout, follow installed package reality and note the mismatch. After wrapping, run import validation and fail the task if any import is unresolved.                                                                                                                                                                                    |
| C7  | **Analyze installed SDK packages in active virtual environment.** Inspect the installed `agentstack_sdk` and `a2a` modules in the active environment and revisit all imports to ensure they match actual installed files, avoiding hallucinations. See also [source structure](https://github.com/i-am-bee/agentstack/tree/main/apps/agentstack-sdk-py/src/agentstack_sdk).                                                                                                                                                      |
| C8  | **Structured Parameters to Forms.** For single-turn agents with named parameters, map them to an `initial_form` using `FormServiceExtensionSpec.demand(initial_form=...)`.                                                                                                                                                                                                                                                                                                                                                       |
| C9  | **Remove CLI arguments.** Remove all `argparse` or `sys.argv` logic. Replace mandatory CLI inputs with `initial_form` items or AgentStack Environment Variables.                                                                                                                                                                                                                                                                                                                                                                 |
| C10 | **Approval gate for business-logic changes.** If compatibility requires business-logic changes, stop and request explicit approval with justification before proceeding.                                                                                                                                                                                                                                                                                                                                                         |
| C11 | **Keep adaptation reversible.** Isolate wrapper and integration changes, avoid destructive refactors, and preserve a rollback path.                                                                                                                                                                                                                                                                                                                                                                                              |
| C12 | **Preserve original helpers.** Do not delete original business-logic helpers unless strictly required. If removal is necessary, document why.                                                                                                                                                                                                                                                                                                                                                                                    |
| C13 | **Optional extension safety.** Service/UI extensions are optional. Check presence/data before use (e.g., `if llm and llm.data ...`).                                                                                                                                                                                                                                                                                                                                                                                             |

---

## Step 1 – Classify the Agent

Read the agent's code and classify it:

| Pattern         | Classification             | Indicators                                                                                                              |
| --------------- | -------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| **Single-turn** | One request → one response | CLI entrypoint, `argparse` (must be removed), primarily stateless business logic, context persistence still recommended |
| **Multi-turn**  | Conversation with memory   | Chat loop, message history, session state, memory object                                                                |

This classification determines:

- How to use `context.store()` and `context.load_history()`: persist input/response by default for all agents; `context.load_history()` is required for multi-turn, and optional for single-turn (use only when prior context is intentionally part of behavior)
- Whether to define an `initial_form` for structured inputs (single-turn with named parameters)

---

## Step 2 – Add and Install Dependencies

1. Find the existing dependency file:
   - `requirements.txt` → append `agentstack-sdk~=<VERSION>`
   - `pyproject.toml` → add to `[project.dependencies]` or `[tool.poetry.dependencies]`
   - add `a2a-sdk` only when direct pinning is required by the project dependency policy
2. **Fetch and pin current version (required).** Before adding, find the current `agentstack-sdk` version on PyPI:
   ```bash
   # agentstack-sdk
   curl -s https://pypi.org/pypi/agentstack-sdk/json | grep -o '"version":"[^"]*"' | head -1 | cut -d'"' -f4
   ```
   If network access is unavailable, use versions already present in the project's lockfile or active environment.
   If the project requires direct `a2a-sdk` pinning, use a version compatible with the selected `agentstack-sdk` dependency constraints.
3. **Install the dependencies.** Once added to the manifest, install them in your virtual environment (e.g., `pip install -r requirements.txt`).
4. **Do not** create a new manifest type the project doesn't already use.
5. **Do not** force `uv` if the project uses `pip`.

**Source-of-truth rule:** Use current official docs and installed package inspection as the authority. If they conflict, follow installed package behavior and report the mismatch.

### Import Recovery Sequence (required)

If import validation fails, follow this exact order:

1. Run import validation to identify missing modules.
2. If a missing import is caused by absent dependencies, install or repair dependencies in the existing manifest workflow.
3. Re-run import validation after dependency repair.
4. If imports still fail, stop and report unresolved imports with module names and file paths.

---

## Step 3 – Create the Server Wrapper

Create a new file (e.g. `agent.py` or `server.py`) with the wrapping code, or modify the original agent files directly. The original code **can** be changed for AgentStack compatibility (e.g. accepting config as parameters instead of reading env vars), but the agent's business logic must not be altered.

Prefer additive wrapper files and minimal adapters over invasive refactors to keep migration reversible.

If the original repository exposes legacy HTTP endpoints that are asserted by tests or explicit contracts, preserve those endpoints or provide compatibility shim routes.

Follow the wrapping pattern from the official guide: **[Wrap Your Existing Agents](https://agentstack.beeai.dev/stable/deploy-agents/wrap-existing-agents.md)**

For building agents from scratch or understanding the full server pattern: **[Build New Agents](https://agentstack.beeai.dev/stable/deploy-agents/building-agents.md)**

Real-world examples of wrapped agents are available at: **[agents/ on GitHub](https://github.com/i-am-bee/agentstack/tree/main/agents)**

### Metadata Extraction

Before writing the code, analyze the original source (docstrings, CLI help, README) to populate the `@server.agent()` parameters:

- **Identity**: Set `name` and `version`.
- **Documentation**: Use `documentation_url` pointing to the source.
- **Detail**: Populate `AgentDetail` with `interaction_mode` (Step 1), `tools`, `author`, and `programming_language`.
- **Skills**: Define `AgentSkill` entries with `id`, `name`, `description`, `tags`, and `examples`.
- **Function Docstring**: The wrapper function's docstring should be a concise summary shown in registries.
- **Extensions**: Identify if the agent needs optional platform capabilities (Step 8) like Citations, Secrets, or Trajectory.

### Key elements

| Element                        | Purpose                                                                                           |
| ------------------------------ | ------------------------------------------------------------------------------------------------- |
| `Server()`                     | Creates the AgentStack server instance                                                            |
| `@server.agent()`              | Registers the function as an agent; function name becomes agent ID, docstring becomes description |
| `input: Message`               | A2A message from the caller; use `get_message_text(input)` to extract the text                    |
| `context: RunContext`          | Execution context (`task_id`, `context_id`, session store, history)                               |
| `yield AgentMessage(text=...)` | Stream one or more response chunks back to the caller                                             |
| `emit trajectory output`       | Surface meaningful intermediate logs/progress separately from final user-facing response          |
| `server.run(host, port)`       | Starts the HTTP server                                                                            |

### Single-turn

Extract the user message with `get_message_text(input)`, call the original agent logic, and `yield AgentMessage(text=result)`. Persist both input and response via `context.store()` unless explicit stateless behavior is required. Only call `context.load_history()` in single-turn mode if continuity is intentionally part of the agent behavior.

If you include trajectory for a single-turn agent, route progress steps to trajectory output and keep the final user response separate.

### Multi-turn

Conversations with memory require explicit history management. Single-turn agents should still persist context unless there is an explicit stateless requirement.

1. **Store input:** Save the incoming user message immediately with `await context.store(input)`.
2. **Load history:** Retrieve the past conversation via `[msg async for msg in context.load_history() if isinstance(msg, Message)]`.
3. **Execute agent:** Pass the history to the original agent logic.
4. **Yield response:** Return chunks with `yield AgentMessage(text=...)`.
5. **Store response:** Save the final agent response(s) with `await context.store(response)` using a generated `Message` object or the yielded `AgentMessage`.

---

## Step 4 – Wire LLM / Services via Extensions

**OpenAI-compatible interface required.** The agent must be designed to work with an OpenAI-compatible interface. If the original agent uses a different LLM provider (e.g., Anthropic, Google), you must install the necessary library (e.g., `langchain-openai`) and use that provider class, passing the configuration received from the LLM extension.

**Do not read API keys from environment variables.** Use AgentStack's platform extensions to receive LLM configuration at runtime.

Add `llm: Annotated[LLMServiceExtensionServer, LLMServiceExtensionSpec.single_demand()]` as an agent function parameter. Extract the config from `llm.data.llm_fulfillments["default"]` and pass `api_key`, `api_base`, `api_model` explicitly to the original agent.

If the `default` fulfillment is missing, declare a secrets parameter (for example `secrets: Annotated[SecretsExtensionServer, SecretsExtensionSpec.single_demand(...)]`), request required secrets through that declared parameter, then construct fulfillment-compatible values and pass `api_key`, `api_base`, and `api_model` explicitly.

Do not reference `secrets.request_secrets()` unless a `secrets` extension parameter is declared on the agent function.

If the original agent reads env vars for API keys internally, refactor it so keys are passed as explicit parameters instead.
Always pass runtime LLM config explicitly, avoid provider/default fallback chains, and fail fast with a clear error if required values are missing.

See the [chat agent](https://github.com/i-am-bee/agentstack/blob/main/agents/chat/src/chat/agent.py) and [competitive-research agent](https://github.com/i-am-bee/agentstack/blob/main/agents) on GitHub for real examples of LLM extension wiring.

---

## Step 5 – Error Handling

Use the **Error extension** for user-visible failures. Do not report errors via a normal `AgentMessage`.

### Implementation

1. **Standard Reporting**: Simply `raise` an exception (e.g., `ValueError`, `RuntimeError`) inside the agent. The platform automatically catches and formats it.
2. **Advanced Configuration**: Add `error_ext: Annotated[ErrorExtensionServer, ErrorExtensionSpec(params=ErrorExtensionParams(include_stacktrace=True))]` as an agent function parameter to enable stack traces in the UI.
3. **Adding Context**: You can attach diagnostic data to `error_ext.context` (a dictionary) before raising an error. This context is serialized to JSON and shown in the UI.
4. **Multiple Errors**: Use `ExceptionGroup` (Python 3.11+) to report multiple failures simultaneously. The extension will render them as a group in the UI.

### Example

```python
@server.agent()
async def my_agent(input: Message, error_ext: Annotated[ErrorExtensionServer, ErrorExtensionSpec()]):
    error_ext.context["op"] = "fetch_data"
    try:
        # ... logic ...
        pass
    except Exception as e:
        error_ext.context["failed_id"] = "123"
        raise RuntimeError(f"Operation failed: {e}") from e
```

See the [chat agent](https://github.com/i-am-bee/agentstack/blob/main/agents/chat/src/chat/agent.py) and [official error guide](https://agentstack.beeai.dev/stable/agent-integration/error.md) for more.

---

## Step 6 – Forms (Single-Turn Structured Input)

If the original agent accepts **named parameters** (not just free text), map them to an `initial_form` using the Forms extension.

1. Define a `FormRender` with appropriate field types (`TextField`, `DateField`, `CheckboxField`, etc.)
2. Create a Pydantic `BaseModel` matching the form fields
3. Add `form: Annotated[FormServiceExtensionServer, FormServiceExtensionSpec.demand(initial_form=form_render)]` as an agent parameter
4. Parse input via `form.parse_initial_form(model=MyParams)`

Only use forms when the agent has clearly defined, structured parameters. For free-text agents, the plain message input is sufficient.

For mid-conversation input:

- Single free-form question, use A2A `input-required` event.
- Structured multi-field input, use dynamic form request extension (`FormRequestExtensionServer` / `FormRequestExtensionSpec`).

See the [form agent example](https://github.com/i-am-bee/agentstack/blob/main/agents/form/src/form/agent.py) on GitHub for a complete implementation.

---

## Step 7 – Entrypoint

Create a `run()` / `serve()` function that calls `server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)), context_store=PlatformContextStore())` with an `if __name__ == "__main__"` guard.

The server defaults to an in-memory context store when `context_store` is omitted, so wrappers that persist or read context history must pass `PlatformContextStore()` explicitly.

For wrappers that implement context or history persistence via `context.store()` or `context.load_history()`, `context_store=PlatformContextStore()` is required.

**Remove all CLI argument parsing** (`argparse.ArgumentParser`, etc.). If the agent previously relied on CLI arguments for input (e.g. `--repo-url`), refactor the input to come from its wrapper function parameters (mapped from a Form or environment variable).

Only add `configure_telemetry` or `auth_backend` if the user explicitly requests platform integration.

---

## Step 8 – Use Platform Extensions

Enhance the agent with platform-level capabilities by injecting extensions via `Annotated` function parameters. Use them if the original agent's behavior warrants it.

| Extension      | When to Use                                                                           | Documentation                                                                                                                                                                                       |
| -------------- | ------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Citations**  | Agent references documents or external URLs                                           | [Citations](https://agentstack.beeai.dev/stable/agent-integration/citations.md)                                                                                                                     |
| **Trajectory** | Multi-step reasoning, tool calls, long-running progress, or explicit debugging traces | [Trajectory](https://agentstack.beeai.dev/stable/agent-integration/trajectory.md)                                                                                                                   |
| **Secrets**    | Agent needs user-provided API keys or tokens at runtime                               | [Secrets](https://agentstack.beeai.dev/stable/agent-integration/secrets.md) (Note: Check `secrets.data` and use `request_secrets` only through a declared `secrets` extension parameter if missing) |
| **Settings**   | Agent has configurable behavior (e.g., "Thinking Mode")                               | [Settings](https://agentstack.beeai.dev/stable/agent-integration/agent-settings.md)                                                                                                                 |
| **Canvas**     | Agent needs to edit artifacts or code selected by user                                | [Canvas](https://agentstack.beeai.dev/stable/agent-integration/canvas.md)                                                                                                                           |
| **Approval**   | Agent performs sensitive tool calls requiring user consent                            | [Tool Call Approval](https://agentstack.beeai.dev/stable/agent-integration/tool-calls.md)                                                                                                           |
| **MCP**        | Agent uses Model Context Protocol tools/servers                                       | [MCP Integration](https://agentstack.beeai.dev/stable/agent-integration/mcp.md)                                                                                                                     |

For a complete overview of all available extensions: **[Agent Integration Overview](https://agentstack.beeai.dev/stable/agent-integration/overview.md)**

### Trajectory Output Rule

Trajectory is optional for simple single-step responders.

Trajectory is required whenever the agent emits meaningful intermediate logs, execution steps, tool activity, or progress updates. Those intermediate signals must be surfaced as trajectory output, and the final user answer should remain focused on the final result.

Trajectory entries are metadata for transparency and observability. They are not a substitute for the agent's user-facing response message.

User-facing text should be emitted as normal `AgentMessage` output. Trajectory should contain the intermediate context behind that answer.

For third-party framework callbacks (for example sync-only step callbacks), capture callback data and emit it later from the main agent handler so trajectory output remains consistent.

---

## Step 9 – Update README

Update the project's `README.md` (or create one if missing) with instructions on how to run the wrapped agent server. Include:

1. **Install dependencies** using the project's existing tooling (e.g. `uv pip install -r requirements.txt` or `pip install -r requirements.txt`).
2. **Run the server** with the appropriate command (e.g. `uv run server.py` or `python server.py`).
3. **Default address** — mention that the server starts at `http://127.0.0.1:8000` by default and can be configured via `HOST` and `PORT` environment variables.

Remove or replace any outdated CLI usage examples (e.g. `argparse`-based commands) that no longer apply after wrapping.

---

## Anti-Patterns

When building and testing the wrapper, ensure you avoid these common pitfalls:

- **Never hardcode API keys or LLM endpoints.** Use the LLM proxy extension explicitly.
- **Never assume history is auto-saved.** If you need context continuity, explicitly call `await context.store(input)` and `await context.store(response)`.
- **Never assume persistent history without `PlatformContextStore`.** Without it, context storage is in-memory and lost on process restart.
- **Never forget to filter history.** `context.load_history()` returns all items in the conversation (Messages, Artifacts). Always filter them using `isinstance(message, Message)`.
- **Never store individual streaming chunks.** Accumulate the full response and store once using `context.store()`.
- **Never hallucinate import paths.** You must never guess imports. `a2a` and `agentstack_sdk` are two separate packages. Always find the exact import name by inspecting the installed packages, and explicitly verify their functionality by running an import check.
- **Never assume extension availability.** Check extension objects and payloads before using them.
- **Never access `.text` directly on a `Message` object.** Message content is multipart. Always use `get_message_text(input)`.
- **Never use synchronous functions for the agent handler.** Agent functions must be `async def` generators using `yield`.
- **Never hide platform integration behind wrapper classes.** Keep decorators, imports, and config visible in the main agent entrypoint file. Enterprise developers must be able to inspect exactly what the agent does.
- **Never force trajectory on trivial wrappers.** For simple single-step text responders, trajectory is optional.
- **Never skip trajectory when meaningful intermediate logs or tool traces are emitted.** Those signals must be surfaced as trajectory output.
- **Never treat trajectory as the final answer channel.** Trajectory is primarily metadata. User-visible answers must still be emitted as normal `AgentMessage` text.
- **Never bury meaningful intermediate logs in the final answer text.** Keep progress/execution visibility separate from the final user-facing response.
- **Never silently remove existing optional auth inputs.** If the original agent supported optional tokens/keys for higher limits or private resources, preserve that optional path or document an approved behavior change.
- **Never use forms for a single free-form question.** Use the A2A `input-required` event instead if a simple free-text answer is needed.
- **Never mismatch form field IDs and model fields.** When using Forms, mismatching IDs means values will fail to parse or silently drop.
- **Never skip null-path handling for forms.** Handle `None` for cancelled or unsubmitted forms.
- **Never treat extension data as dictionaries.** Data attached to extensions (e.g., `llm.data.llm_fulfillments["default"]`) are Pydantic objects, not dicts. Always access properties using dot notation (e.g., `config.api_key`, not `config.get("api_key")`).
- **Never use `llm_config.identifier` as the model name.** `identifier` points to the provider binding (for example `llm_proxy`), not to the deployable model. Use `llm_config.api_model` for model selection.
- **Never apply silent fallback when `llm.data.llm_fulfillments["default"]` is missing.** Either request secrets through a declared `secrets` extension and construct explicit `api_key`/`api_base`/`api_model` values, or raise a clear error.
- **Never rely on framework default LLM fallback chains.** If the wrapped runtime tries alternate providers automatically, disable that path by passing explicit provider/client config from the extension contract.
- **Never rewrite agent business logic.** Only wrap the existing entry point. Never attempt to "fix" the original agent's internal workings.

## Failure Conditions

- If the project's primary language is not Python, stop and report unsupported runtime.
- If fresh docs cannot be fetched, stop and report that execution cannot continue without current docs.

---

## Finalization Report (Required)

Before completion, provide all of the following:

1. **Mapping summary:** inbound mapping (A2A Message to agent input), outbound mapping (agent output to `AgentMessage`), and selected streaming path.
2. **Behavior changes list:** if behavior changed, list each change with reason and impact.
3. **Business-logic statement:** state whether business logic changed, and if it did, include approval and justification.
4. **Legacy endpoint compatibility result:** state preserved, shimmed, or not applicable.
5. **Dockerfile prompt:** Ask the user if they also want to add a `Dockerfile`. If the user says yes, review the example at `https://github.com/i-am-bee/agentstack-starter/blob/main/Dockerfile` and assemble a `Dockerfile` for the project. Do not force the use of `uv` if the project does not use it.
6. **Testing prompt:** Ask the user if they want to test the agent functionality. If they say yes, start the agent first in one terminal, and then use a separate terminal to run `agentstack run AGENT_NAME`. Do not attempt to interrupt the `run` command, as it may take a long time to complete. If the execution fails and an error is encountered, attempt to fix the error and run the test again. **Critically, do not create any new files or scripts (e.g., Python test scripts using pexpect) to perform this test. You must interact with the terminals directly.**

---

## Verification Checklist

After wrapping, confirm:

- [ ] Every `import` resolves to a real, installed module
- [ ] The agent function has a meaningful docstring (used as description in UI)
- [ ] `yield AgentMessage(text=...)` is used for all responses
- [ ] No env vars are used for API keys or model config (extensions used instead)
- [ ] Agent uses an OpenAI-compatible interface or has necessary provider libraries installed for other LLMs
- [ ] Wrapper passes explicit runtime LLM config from extensions and does not rely on framework/provider fallback defaults
- [ ] Single-turn vs multi-turn classification matches the actual agent behavior
- [ ] If single-turn with structured params → `initial_form` is defined
- [ ] `input` and `response` are stored via `context.store()` unless explicit stateless behavior is justified
- [ ] `context.load_history()` is required for multi-turn; for single-turn, it is used only when continuity is intentionally required
- [ ] No business-logic changes were made to the original agent code unless explicitly approved per Constraint C10
- [ ] If business-logic change was required, explicit approval and justification are recorded
- [ ] No Dockerfile was added unless explicitly requested
- [ ] Temp files created at runtime are cleaned up
- [ ] `agentstack-sdk` (pinned with `~=`) was added to the project's **existing** dependency file
- [ ] If `a2a-sdk` is pinned directly, its version is explicitly compatible with the selected `agentstack-sdk`
- [ ] Errors raise exceptions (handled by Error extension), not yielded as `AgentMessage`
- [ ] Optional extensions are checked for presence/data before use
- [ ] If the agent references sources -> **Citations extension** is used
- [ ] If the agent has meaningful multi-step execution/tool traces, trajectory output is emitted for those steps
- [ ] Final user-facing answer is emitted as normal `AgentMessage` output, not only as trajectory data
- [ ] If the agent already used secrets -> **Secrets extension** is used (safe access pattern with `request_secrets` through a declared secrets extension parameter). No new secrets added.
- [ ] No extra middleware, auth, or containerization added unless explicitly requested (Constraint C2)
- [ ] Imports follow import truth and validation rule (Constraint C6)
- [ ] No command-line arguments (`argparse`) remain in the code (Constraint C9)
- [ ] You have provided a **Mapping summary** showing inbound mapping (A2A Message to agent input), outbound mapping (agent output to AgentMessage), and streaming path selected.
- [ ] `context_store=PlatformContextStore()` is present whenever the wrapper persists or reads context history.
- [ ] If legacy HTTP endpoints were contract-tested, compatibility is preserved or shimmed.
- [ ] If behavior changed, the Finalization Report includes an explicit change list and impact.
- [ ] Agent responds at `/.well-known/agent-card.json` with HTTP 200 and a valid and parseable JSON.
- [ ] Agent card includes required identity fields used for discovery.
- [ ] **Validate the Agent Card** by running script `validate-agent-card.py` (Make sure the agent is running, and pass `server:port` if it's not on the default `127.0.0.1:8000`). **Show the full output of this validation script to the user.**
- [ ] The user was asked if they want to add a `Dockerfile` (and if requested, it was generated based on the agentstack-starter example without forcing `uv`).
- [ ] The user was asked if they want to test the agent's functionality. If they said yes, the agent was started first, and then in a separate terminal, the `agentstack run AGENT_NAME` command was executed (**do not activate the virtual environment before running this command**). The `run` command was allowed to run without interruption, and any errors encountered were investigated, fixed, and the test was rerun. **No additional files or test scripts were created during testing.**
