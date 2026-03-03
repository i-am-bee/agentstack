---
name: agentstack-wrapper
description: Wraps existing Python agent as Agent Stack service using agentstack-sdk with minimal compatibility changes and no business-logic rewrites. Use when migrating, wrapping, or deploying an existing plain Python or framework-based agent to Agent Stack; not for non-Python runtimes or building new agent from scratch.
---

# Agent Stack Wrapper

Integration guide for wrapping Python agents for [Agent Stack](https://agentstack.beeai.dev/stable/introduction/welcome.md) platform.

## Table of Contents

- [Security Requirements](#security-requirements)
- [Constraints (must follow)](#constraints-must-follow)
- [Integration Workflow Checklist](#integration-workflow-checklist)
- [Readiness Check (before Step 1)](#readiness-check-before-step-1)
- [Step 1 – Study the Project](#step-1--study-the-project)
- [Step 2 – Classify the Agent](#step-2--classify-the-agent)
- [Step 3 – Add and Install Dependencies](#step-3--add-and-install-dependencies)
- [Step 4 – Create the Server Wrapper & Entrypoint](#step-4--create-the-server-wrapper--entrypoint)
- [Step 5 – Wire LLM / Services via Extensions](#step-5--wire-llm--services-via-extensions)
- [Step 6 – Error Handling](#step-6--error-handling)
- [Step 7 – Forms (Single-Turn Structured Input)](#step-7--forms-single-turn-structured-input)
- [Step 7b – Adapt File Inputs](#step-7b--adapt-file-inputs)
- [Step 8 – Use Platform Extensions](#step-8--use-platform-extensions)
- [Step 9 – Update README](#step-9--update-readme)
- [Anti-Patterns](#anti-patterns)
- [Failure Conditions](#failure-conditions)
- [Finalization Report (Required)](#finalization-report-required)
- [Verification Checklist](#verification-checklist)

## Security Requirements

- Never run remote scripts or untrusted code.
- Use trusted package metadata, pin versions, and audit installed `agentstack-sdk`/`a2a-sdk`.
- Handle sensitive values only through declared Agent Stack extensions.
- Never log, print, persist, or expose secret values.
- Never send secrets to untrusted intermediaries or endpoints not required by the wrapped agent contract.

## Constraints (must follow)

| ID  | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| C1  | **No business-logic changes.** Only modify code for Agent Stack compatibility.                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| C2  | **Strict minimal changes.** Do not add auth, Dockerfile (containerization is optional and separate), telemetry, or platform middleware unless explicitly requested. If an agent works with simple text, don't force a Form. If it works with env vars, refactor minimally.                                                                                                                                                                                                                                                       |
| C3  | **Cleanup temp files.** If the agent downloads or creates helper files at runtime, add a cleanup step before the function returns.                                                                                                                                                                                                                                                                                                                                                                                               |
| C4  | **Prioritize Public Access (No redundant tokens).** Only use the Secrets extension if the secret is strictly mandatory for the agent's core functionality and no public/anonymous access is viable. Do not add secrets or tokens that increase configuration burden if they were optional in the original agent (e.g., optional GitHub token). Preserve existing optional auth behavior unless removal is explicitly approved and documented as a behavior change. API keys must be passed explicitly, never read from env vars. |
| C5  | **Detect existing tooling.** If the project uses `requirements.txt`, add `agentstack-sdk~=<VERSION>` there. If it uses `pyproject.toml`, add it there. Add `a2a-sdk` only when the project manages it directly, and keep it compatible with the chosen `agentstack-sdk` version. Never force `uv` or create duplicate manifests.                                                                                                                                                                                                 |
| C6  | **Import Truth and Validation.** All imports must match modules that exist in the active virtual environment (`agentstack_sdk`, `a2a`). If official docs conflict with installed package layout, follow installed package reality and note the mismatch. After wrapping, run import validation and fail the task if any import is unresolved.                                                                                                                                                                                    |
| C7  | **Analyze installed SDK packages in active virtual environment.** Inspect the installed `agentstack_sdk` and `a2a` modules in the active environment and revisit all imports to ensure they match actual installed files, avoiding hallucinations. See also [source structure](https://github.com/i-am-bee/agentstack/tree/main/apps/agentstack-sdk-py/src/agentstack_sdk).                                                                                                                                                      |
| C8  | **Structured Parameters to Forms.** For single-turn agents with named parameters, map them to an `initial_form` using `FormServiceExtensionSpec.demand(initial_form=...)`.                                                                                                                                                                                                                                                                                                                                                       |
| C9  | **Remove CLI arguments.** Remove all `argparse` or `sys.argv` logic. Replace mandatory CLI inputs with `initial_form` items, AgentStack Settings Extension (for runtime options), or AgentStack Env Variables.                                                                                                                                                                                                                                                                                                                   |
| C10 | **Approval gate for business-logic changes.** If compatibility requires business-logic changes, stop and request explicit approval with justification before proceeding.                                                                                                                                                                                                                                                                                                                                                         |
| C11 | **Keep adaptation reversible.** Isolate wrapper and integration changes, avoid destructive refactors, and preserve a rollback path.                                                                                                                                                                                                                                                                                                                                                                                              |
| C12 | **Preserve original helpers.** Do not delete original business-logic helpers unless strictly required. If removal is necessary, document why.                                                                                                                                                                                                                                                                                                                                                                                    |
| C13 | **Optional extension safety.** Service/UI extensions are optional. Check presence/data before use (e.g., `if llm and llm.data ...`).                                                                                                                                                                                                                                                                                                                                                                                             |
| C14 | **No secret exposure.** Never log, print, persist, or echo secret values (API keys, tokens, passwords). Redact sensitive values in logs and errors.                                                                                                                                                                                                                                                                                                                                                                              |
| C15 | **No remote script execution.** Never run untrusted remote code during wrapping. Use project manifests and trusted package metadata only.                                                                                                                                                                                                                                                                                                                                                                                        |
| C16 | **Constrained outbound targets.** Do not introduce arbitrary network targets. Limit external calls to trusted dependency sources and runtime endpoints explicitly required by the wrapped agent contract.                                                                                                                                                                                                                                                                                                                        |
| C17 | **No dynamic command execution from input.** Do not introduce wrapper patterns that execute shell commands from user/model input (for example, `eval`, `exec`, `os.system`, or unsanitized `subprocess` calls).                                                                                                                                                                                                                                                                                                                  |
| C18 | **Read Wrapper Documentation First.** Before starting any implementation, you must read the official guide: [Wrap Your Existing Agents](https://agentstack.beeai.dev/stable/deploy-agents/wrap-existing-agents.md).                                                                                                                                                                                                                                                                                                              |
| C19 | **Read Extension Documentation.** Before implementing any extension (Forms, LLM, Error, etc.), you **MUST** read its corresponding documentation URL (listed in Step 9) and extract the exact imports, class names, method names, properties, and their exact types directly from the official documentation. Do not guess these values. Only modify the agent code after reading the documentation.                                                                                                                             |
| C20 | **Replace filesystem file inputs with platform file uploads.** If the original agent reads files from the local filesystem (e.g., `open()`, `pathlib.Path`, CLI file path arguments), replace those inputs with `FileField` form uploads and the platform `File` API. Do not assume local filesystem access at runtime. See Step 7b.                                                                                                                                                                                             |

**CRITICAL WORKFLOW REQUIREMENT:** For _every_ extension you decide to use (whether from LLM/Forms/Error steps or Platform Extensions), you MUST follow these exact steps in order:

1. Decide if the extension should be implemented.
2. If yes, **READ the documentation URL provided in the extension table below** (e.g., using a tool to read the webpage).
3. Extract the correct imports, class names, method names, properties, and their exact types directly from the official documentation.
4. **Only AFTER reading the documentation**, proceed to write or modify the agent code. Never guess imports or rely on outdated memory.

---

## Integration Workflow Checklist

Copy this checklist into your context and check off items as you complete them:

```
Task Progress:
- [ ] Readiness Check (before Step 1)
- [ ] Step 1: Study the Project
- [ ] Step 2: Classify the Agent
- [ ] Step 3: Add and Install Dependencies
- [ ] Step 4: Create the Server Wrapper & Entrypoint
- [ ] Step 5: Wire LLM / Services via Extensions (requires reading docs)
- [ ] Step 6: Implement Error Handling (requires reading docs)
- [ ] Step 7: Map Forms (if applicable) (requires reading docs)
- [ ] Step 7b: Adapt File Inputs (if applicable) (requires reading docs)
- [ ] Step 8: Use Platform Extensions (requires reading docs for each chosen extension)
- [ ] Step 9: Update README
- [ ] Finalization Report (required)
- [ ] Verification Checklist (required)

```

**STOP GATE:** After Step 9, you MUST complete the Finalization Report and walk through every item in the Verification Checklist before reporting completion. The task is NOT done until both are finished.

## Readiness Check (before Step 1)

- [ ] Python 3.12+ is available.
- [ ] Agent source code is available locally.
- [ ] The project dependency workflow is identified.

If any item fails, stop and ask the user.

## Step 1 – Study the Project

Before making any changes, you must thoroughly study the existing project to understand its architecture and requirements.

If there is a `README.md` or `AGENTS.md` file, read it first to better understand the structure and purpose of the agent.

Evaluate and document the following:

- **Core Functionality**: What does the agent do? What are its primary inputs and outputs?
- **Dependencies**: What external systems, APIs, or databases does the agent depend on?
- **Configuration**: How is the agent configured (e.g., environment variables, configuration files, CLI arguments)?
- **Tools & Libraries**: What primary libraries does it use for LLM interaction (e.g., LangChain, bare OpenAI SDK)?

## Step 2 – Classify the Agent

Read the agent's code and classify it:

| Pattern         | Classification             | Indicators                                                                                                              |
| --------------- | -------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| **Single-turn** | One request → one response | CLI entrypoint, `argparse` (must be removed), primarily stateless business logic, context persistence still recommended |
| **Multi-turn**  | Conversation with memory   | Chat loop, message history, session state, memory object                                                                |

This classification determines:

- How to use `context.store()` and `context.load_history()`: persist input/response by default for all agents; `context.load_history()` is required for multi-turn, and optional for single-turn (use only when prior context is intentionally part of behavior)
- Whether to define an `initial_form` for structured inputs (single-turn with named parameters)

---

## Step 3 – Add and Install Dependencies

1. Find the existing dependency file:
   - `requirements.txt` → append `agentstack-sdk~=<VERSION>`
   - `pyproject.toml` → add to `[project.dependencies]` or `[tool.poetry.dependencies]`
   - add `a2a-sdk` only when direct pinning is required by the project dependency policy
2. **Select and pin a trusted version (required).** If the project already pins `agentstack-sdk` in its lockfile/constraints or active environment, use that compatible version and keep consistency with the project. If no version is present, use the latest compatible stable released `agentstack-sdk` version from trusted PyPI metadata, then pin with `~=`.
   If the project requires direct `a2a-sdk` pinning, use a version compatible with the selected `agentstack-sdk` dependency constraints.
3. **Install the dependencies.** Once added to the manifest, install them in your virtual environment (e.g., `pip install -r requirements.txt`).
4. **Do not** create a new manifest type the project doesn't already use.
5. **Do not** force `uv` if the project uses `pip`.

### Version Pins

- `agentstack-sdk`
  - If already pinned compatibly: keep it.
  - Otherwise: pin a trusted stable release with `~=`.
- `a2a-sdk`
  - If the project directly manages it: keep/add a version compatible with the selected `agentstack-sdk`.
  - If not: do not add a direct pin.
- Never bump `a2a-sdk` just to follow "latest" when constraints disagree.

**Source-of-truth rule:** Use current official docs and installed package inspection as the authority. If they conflict, follow installed package behavior and report the mismatch.

**Security rule:** Do not execute remote installation scripts. Use only the repository's existing dependency workflow and trusted package sources.

### Import Recovery Sequence (required)

If import validation fails, follow this exact order:

1. Run import validation to identify missing modules.
2. If a missing import is caused by absent dependencies, install or repair dependencies in the existing manifest workflow.
3. Re-run import validation after dependency repair.
4. If imports still fail, stop and report unresolved imports with module names and file paths.

### Exploring Unknown Packages Without Test Files (Zero-File Discovery)

**Primary Method (Documentation Search):**
First, you MUST attempt to find the exact import path, class names, method names, and properties in the official Agent Stack documentation. Use your web search or documentation reading tools to locate the correct information.

**Fallback Method (Inline Package Search):**
If you need to figure out exact imports from installed libraries (`agentstack_sdk`, `a2a`) but docs are unavailable, **do not create temporary test scripts**. Instead, use inline Python execution (`python -c`) or your native search tools to map imports without polluting the project repository.

Use this approach **only** if you ran the code and it failed due to a missing or incorrect import. You have several options for inline exploration depending on what you need:

**1. Quick Overview with `dir()`:**
The simplest way to see what's available in a module is the built-in `dir()` function, which returns a list of all names (variables, functions, classes, modules) in the given object's namespace.

```bash
python -c 'import agentstack_sdk; print(dir(agentstack_sdk))'
```

_Note: This will also show internal attributes (starting with an underscore), which you generally should avoid using._

**2. Official Exports with `__all__`:**
Many well-written packages define an `__all__` list, specifying strictly what should be exported as the public API.

```bash
python -c 'import agentstack_sdk; print(getattr(agentstack_sdk, "__all__", "Module does not define __all__, use dir()"))'
```

**3. Deep Search (for nested/hidden classes):**
**Last Resort:** If you know the exact name of the target class but cannot find its import path in the documentation, use this snippet to crawl the package:

```bash
python -c '
import pkgutil, importlib
def find_class(pkg_name, target):
    pkg = importlib.import_module(pkg_name)
    for _, modname, _ in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
        try:
            if hasattr(importlib.import_module(modname), target):
                print(f"Found {target} in: {modname}")
        except Exception:
            pass
find_class("agentstack_sdk", "AgentDetail")
'
```

Once the module is located, you can inspect its signature or docstring directly via another short inline command:

```bash
python -c "from agentstack_sdk.server.agent import AgentDetail; help(AgentDetail)"
```

---

## Step 4 – Create the Server Wrapper & Entrypoint

Create a new file (e.g., `agent.py`) with wrapping code, adapting original inputs without altering core business logic. Prefer additive files and minimal adapters. Preserve legacy HTTP contract endpoints if asserted by tests.

Prefer additive wrapper files and minimal adapters over invasive refactors to keep migration reversible.

Follow the wrapping pattern from the official guide: **[Wrap Your Existing Agents](https://agentstack.beeai.dev/stable/deploy-agents/wrap-existing-agents.md)**

For building agents from scratch or understanding the full server pattern: **[Build New Agents](https://agentstack.beeai.dev/stable/deploy-agents/building-agents.md)**

Real-world examples of wrapped agents are available at: **[agents/ on GitHub](https://github.com/i-am-bee/agentstack/tree/main/agents)**

### Metadata Extraction

Before writing the code, analyze the original source (docstrings, CLI help, README) to populate the `@server.agent()` parameters:

- **Identity**: Set a user-readable `name` and `version`.
- **Documentation**: Use `documentation_url` pointing to the source.
- **Detail**: Populate `AgentDetail` with `interaction_mode` (Step 2), `tools`, `author` (must be a dictionary, e.g., `{"name": "agentstack"}`), and `programming_language`.
- **Skills**: Define `AgentSkill` entries with `id`, `name`, `description`, `tags`, and `examples`.
- **Function Docstring**: The wrapper function's docstring should be a concise summary shown in registries.
- **Extensions**: Identify if the agent needs optional platform capabilities (Step 8) like Citations, Secrets, or Trajectory.

### Key elements

| Element                                      | Purpose                                                                                           |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `Server()`                                   | Creates the Agent Stack server instance                                                           |
| `@server.agent()`                            | Registers the function as an agent; function name becomes agent ID, docstring becomes description |
| `input: Message`                             | A2A message from the caller; use `get_message_text(input)` to extract the text                    |
| `context: RunContext`                        | Execution context (`task_id`, `context_id`, session store, history)                               |
| `error_ext: Annotated[...]`                  | `ErrorExtensionServer` parameter mapping to `ErrorExtensionSpec()` to configure UI stacktraces    |
| `yield AgentMessage(text=...)`               | Stream one or more response chunks back to the caller                                             |
| `yield AgentArtifact(...)` / `ArtifactChunk` | Return files, documents, or chunks of structured content back to the caller                       |
| `yield AuthRequired(...)`                    | Pause execution to request an OAuth or platform authentication token                              |
| `Metadata(...)`                              | Attach extension metadata (e.g., Citations, Canvas references) to an `AgentMessage`               |
| `emit trajectory output`                     | Surface meaningful intermediate logs/progress separately from final user-facing response          |
| `server.run(host, port)`                     | Starts the HTTP server                                                                            |

### Implementation: Conditional Workflows

Based on the classification in Step 2, follow exactly ONE of these workflows:

#### If the agent is Single-turn:

Follow this checklist for single-turn agents:

```
Single-turn Implementation:
- [ ] Extract user message with `get_message_text(input)`
- [ ] Only call `context.load_history()` if continuity is intentionally required
- [ ] Pass necessary inputs (from forms or text) to original agent logic
- [ ] Route intermediate progress steps to Trajectory output (Optional)
- [ ] Yield the final response via `AgentMessage(text=result)`
- [ ] Persist both input and response via `context.store()`
```

#### If the agent is Multi-turn:

Follow this checklist for agents requiring memory:

```
Multi-turn Implementation:
- [ ] Store input: Save incoming user message immediately with `await context.store(input)`
- [ ] Load history: Retrieve past conversation via `[msg async for msg in context.load_history() if isinstance(msg, Message)]`
- [ ] Execute agent: Pass the filtered history to the original agent logic
- [ ] Route traces: Emit intermediate multi-step reasoning to trajectory extension (Optional)
- [ ] Yield response: Return final answering chunks with `yield AgentMessage(text=...)`
- [ ] Store response: Save the final response with `await context.store(response)`
```

#### Entrypoint

Create a `run()` / `serve()` function protected by an `if __name__ == "__main__":` guard. This function should call `server.run()`:

- The server should be configured to listen on a `host` and `port` from environment variables (e.g., `host=os.getenv("HOST", "127.0.0.1")`, `port=int(os.getenv("PORT", 8000))`).
- If the agent persists or reads context history, you must pass `context_store=PlatformContextStore()` to `server.run()`.
- **Remove all CLI argument parsing** (`argparse`). Map required CLI inputs to the wrapper parameters instead (e.g., from Forms, Settings, or Environment variables).
- Only `auth_backend` if explicitly requested.

---

## Step 5 – Wire LLM / Services via Extensions

**OpenAI-compatible interface required.** The agent must be designed to work with an OpenAI-compatible interface. If the original agent uses a different LLM provider (e.g., Anthropic, Google), you must install the necessary library (e.g., `langchain-openai`) and use that provider class, passing the configuration received from the LLM extension.

**Do not read API keys from environment variables.** Use Agent Stack platform extensions to receive LLM configuration at runtime.
_(Note: Sometimes the exact structure of the credentials provided by the extension can only be fully explored and validated by running the agent and inspecting the injected objects)._

Add `llm: Annotated[LLMServiceExtensionServer, LLMServiceExtensionSpec.single_demand()]` as an agent function parameter. Extract the config from `llm.data.llm_fulfillments["default"]` and pass `api_key`, `api_base`, `api_model` explicitly to the original agent.

If the `default` fulfillment is missing, declare a secrets parameter (for example `secrets: Annotated[SecretsExtensionServer, SecretsExtensionSpec.single_demand(...)]`), request required secrets through that declared parameter, then construct fulfillment-compatible values and pass `api_key`, `api_base`, and `api_model` explicitly.

Do not reference `secrets.request_secrets()` unless a `secrets` extension parameter is declared on the agent function.

If the original agent reads env vars for API keys internally, refactor it so keys are passed as explicit parameters instead.
Always pass runtime LLM config explicitly, avoid provider/default fallback chains, and fail fast with a clear error if required values are missing.

See the [chat agent](https://github.com/i-am-bee/agentstack/blob/main/agents/chat/src/chat/agent.py) and [competitive-research agent](https://github.com/i-am-bee/agentstack/blob/main/agents) on GitHub for real examples of LLM extension wiring.

---

## Step 6 – Error Handling

Use the **Error extension** for user-visible failures. Do not report errors via a normal `AgentMessage`.

### Implementation

1. **Standard Reporting**: Simply `raise` an exception (e.g., `ValueError`, `RuntimeError`) inside the agent. The platform automatically catches and formats it.
2. **Advanced Configuration**: Add `error_ext: Annotated[ErrorExtensionServer, ErrorExtensionSpec(params=ErrorExtensionParams(include_stacktrace=True))]` as an agent function parameter to enable stack traces in the UI.
3. **Adding Context**: You can attach diagnostic data to `error_ext.context` (a dictionary) before raising an error. This context is serialized to JSON and shown in the UI.
4. **Multiple Errors**: Use `ExceptionGroup` (Python 3.11+) to report multiple failures simultaneously. The extension will render them as a group in the UI.

### Example

See the [official error guide](https://agentstack.beeai.dev/stable/agent-integration/error.md) and [chat agent example](https://github.com/i-am-bee/agentstack/blob/main/agents/chat/src/chat/agent.py) for practical implementation examples.

---

## Step 7 – Forms (Single-Turn Structured Input)

If the original agent accepts **named parameters** (not just free text), map them to an `initial_form` using the Forms extension. For free-text agents, the plain message input is sufficient — skip this step.

**Read `references/forms.md` for the full implementation guide** (field types, Pydantic model, mid-conversation input).

---

## Step 7b – Adapt File Inputs

If the original agent reads files from the local filesystem or accepts file paths as CLI/function arguments, those inputs must be replaced with platform file uploads. Local filesystem access is not available at runtime. Even if the file contains plain text, still use a `FileField` upload — do not flatten file inputs into message text.

**Read `references/files.md` for detection patterns, replacement steps, text extraction, and mid-conversation uploads.**

---

## Step 8 – Use Platform Extensions

Enhance the agent with platform-level capabilities by injecting extensions via `Annotated` function parameters. Use them if the original agent's behavior warrants it.

| Extension             | Use when the Agent                                                                          | Documentation                                                                                                                                                                                                      |
| --------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **LLM Proxy Service** | Needs platform-provided language model access and credentials                               | [LLM Proxy Service](https://agentstack.beeai.dev/stable/agent-integration/llm-proxy-service.md)                                                                                                                    |
| **Forms**             | Requires structured, named parameter inputs (not just free text)                            | [Collect Input with Forms](https://agentstack.beeai.dev/stable/agent-integration/forms.md)                                                                                                                         |
| **Trajectory**        | Emits multi-step reasoning, tool calls, long-running progress, or explicit debugging traces | [Visualize Agent Trajectories](https://agentstack.beeai.dev/stable/agent-integration/trajectory.md)                                                                                                                |
| **Files**             | Needs to read image or document files uploaded by the user                                  | [Working with Files](https://agentstack.beeai.dev/stable/agent-integration/files.md)                                                                                                                               |
| **Error**             | Needs to report structured, user-visible failures and stack traces                          | [Handle Errors](https://agentstack.beeai.dev/stable/agent-integration/error.md)                                                                                                                                    |
| **Settings**          | Has configurable behavior (for example, "Thinking Mode")                                    | [Configure Agent Settings](https://agentstack.beeai.dev/stable/agent-integration/agent-settings.md)                                                                                                                |
| **OAuth**             | Accesses OAuth-protected third-party APIs (for example, GitHub or Slack)                    | [OAuth](https://agentstack.beeai.dev/stable/agent-integration/oauth.md)                                                                                                                                            |
| **MCP**               | Uses Model Context Protocol tools or servers                                                | [MCP Integration](https://agentstack.beeai.dev/stable/agent-integration/mcp.md)                                                                                                                                    |
| **Embedding**         | Performs vector search or uses RAG strategies                                               | [Build RAG Pipelines](https://agentstack.beeai.dev/stable/agent-integration/rag.md)                                                                                                                                |
| **Approval**          | Performs sensitive tool calls requiring user consent                                        | [Approve Tool Calls](https://agentstack.beeai.dev/stable/agent-integration/tool-calls.md)                                                                                                                          |
| **Secrets**           | Needs user-provided API keys or tokens at runtime                                           | [Manage Runtime Secrets](https://agentstack.beeai.dev/stable/agent-integration/secrets.md) (Note: Check `secrets.data` and use `request_secrets` only through a declared `secrets` extension parameter if missing) |
| **Env Variables**     | Requires custom environment-level deployment configuration variables                        | [Environment Variables](https://agentstack.beeai.dev/stable/agent-integration/env-variables.md)                                                                                                                    |
| **Canvas**            | Needs to edit artifacts or code selected by the user                                        | [Work with Canvas](https://agentstack.beeai.dev/stable/agent-integration/canvas.md)                                                                                                                                |
| **Citations**         | References documents or external URLs                                                       | [Add Citations to Agent Responses](https://agentstack.beeai.dev/stable/agent-integration/citations.md)                                                                                                             |

For a complete overview of all available extensions: **[Agent Integration Overview](https://agentstack.beeai.dev/stable/agent-integration/overview.md)**

### Configuration Mapping Rule

It is critical to determine if the agent has any configuration and what environment variables it uses. You must investigate the following three sources:

1. **Agent code**: Look for `os.environ.get`, `os.getenv`, `os.environ[...]`, `dotenv`, or configuration classes.
2. **README.md**: Check deployment or configuration instructions.
3. **`.env` or `.env.example`** file if present in the repository.

If you identify variables, you must decide how to handle them. Use the following extension logic:

- **AgentStack Settings Extension**: Best for runtime configuration options that alter agent behavior (e.g., toggles, multiple-choice options like a \"select\" dropdown, \"thinking mode\").
- **AgentStack Env Variables Extension**: Best for low-level system configuration needed just to run the container/service (e.g., `PORT`, `HOST`, database connection strings).
- **AgentStack Secrets Extension**: Best for sensitive user-level settings like API keys for external services.

**IMPORTANT CAUTION**: If you are unsure which extension to use for a particular secret or environment variable (especially regarding API keys to external services), **always ask the user** before making structural changes.

### Secret Handling Rule

**Do not use global environment assignment.** Never use `os.environ["KEY"] = secrets.data["KEY"]`. Instead, pass the secret value directly to the function or class that requires it (e.g., as a client constructor argument or a method parameter). This prevents global side effects and ensures that secrets are correctly scoped to the specific execution context.

### Trajectory Output Rule

Use this decision rule:

- **Required:** emit trajectory for meaningful intermediate activity: multi-step execution, loops, tool calls, or progress updates. If the agent has multiple steps, it almost always needs trajectories.
- **Required (Logs/Prints):** if the original agent uses logging or `print` statements, these are prime candidates to be converted into trajectory entries.
- **Required (hidden internals):** if internal steps are not directly visible, emit trajectory at visible milestones: start, major phase change, completion, and failure.
- **Optional:** for simple single-step responders with no meaningful intermediate activity, trajectory may be omitted.
- **Default:** when uncertain, enable trajectory.

Trajectory entries are metadata for transparency and observability. They are not a substitute for the agent's user-facing response message.

User-facing text should be emitted as normal `AgentMessage` output. Trajectory should contain the intermediate context behind that answer.

If callbacks are sync-only, capture callback data and emit it later from the main agent handler.

### Trajectory Implementation

When implementing trajectories, follow the [Trajectory Documentation](https://agentstack.beeai.dev/stable/agent-integration/trajectory.md) and utilize these patterns:

- **`yield`**: Use `trajectory.trajectory_metadata(title="", content="")` within the main agent generator to emit progress updates.
- **`context.yield_async() or context.yield_sync()`**: to emit trajectory entries from within nested asynchronous functions or utility methods.
- **`trajectory_metadata`**: Use the `metadata` field (often referred to as `trajectory_metadata` in configuration) to provide structured, machine-readable context for each trajectory step.

---

## Step 9 – Update README

Update the project's `README.md` (or create one if missing) with instructions on how to run the wrapped agent server. Include:

1. **Install dependencies** using the project's existing tooling (e.g. `uv pip install -r requirements.txt` or `pip install -r requirements.txt`).
2. **Environment Configuration** — Document required `.env` patterns if `python-dotenv` is used. However, ensure the agent still receives configuration explicitly instead of reading env arguments internally.
3. **Run the server** with the appropriate command (e.g. `uv run server.py` or `python server.py`).
4. **Default address** — mention that the server starts at `http://127.0.0.1:8000` by default and can be configured via `HOST` and `PORT` environment variables.

Remove or replace any outdated CLI usage examples (e.g. `argparse`-based commands) that no longer apply after wrapping.

---

## Anti-Patterns

When building and testing the wrapper, ensure you avoid these common pitfalls:

- **Never access `.text` directly on a `Message` object.** Message content is multipart. Always use `get_message_text(input)`.
- **Never use synchronous functions for the agent handler.** Agent functions must be `async def` generators using `yield`.
- **Never hide platform wiring behind abstraction layers.** Keep `@server.agent(...)`, extension parameters, and integration contracts visible in the main entrypoint so behavior is auditable.
- **Never hallucinate SDK import paths.** `agentstack_sdk` and `a2a` are separate packages; validate imports against the installed environment before finalizing.
- **Never assume history is auto-saved.** Explicitly call `await context.store(input)` and `await context.store(response)`.
- **Never assume persistent history without `PlatformContextStore`.** Without it, context storage is in-memory and lost on restart.
- **Never forget to filter history.** `context.load_history()` returns Messages and Artifacts. Filter with `isinstance(message, Message)`.
- **Never store individual streaming chunks.** Accumulate the full response and store once.
- **Never treat extension data as dictionaries.** Use dot notation (e.g., `config.api_key`, not `config.get("api_key")`).
- **Never use `llm_config.identifier` as the model name.** Use `llm_config.api_model` instead.
- **Never assume all extension specs have `.demand()`.** Some use `.single_demand()` or direct instantiation. Always verify.
- **Never silently remove existing optional auth paths.** If the source agent supported optional tokens/keys, preserve that optional behavior unless an approved behavior change is explicitly documented.
- **Never use Forms for a single free-form follow-up.** Use A2A `input-required` for one-question free text prompts; reserve Forms for structured multi-field input.
- **Never mismatch form field IDs and model fields.** Mismatched IDs cause silent parse failures.
- **Never guess platform object attributes.** `FormRender` uses `fields` (not `items`), `TextField` uses `label` (not `title`).
- **Never skip null-path handling for forms.** Handle `None` for cancelled or unsubmitted forms.
- **Never assume uploaded file URIs are HTTP URLs.** Parse `agentstack://` URIs with `PlatformFileUrl`.
- **Never skip extraction polling.** `create_extraction()` is async — poll `get_extraction()` until `status == 'completed'`.

## Failure Conditions

- If fresh docs cannot be fetched, stop and report that execution cannot continue without current docs.

---

## Finalization Report (Required)

Before completion, provide all of the following:

1. **Mapping summary:** inbound mapping (A2A Message to agent input), outbound mapping (agent output to `AgentMessage`), and selected streaming path.
2. **Behavior changes list:** if behavior changed, list each change with reason and impact.
3. **Business-logic statement:** state whether business logic changed, and if it did, include approval and justification.
4. **Legacy endpoint compatibility result:** state preserved, shimmed, or not applicable.
5. **Dockerfile prompt:** Ask the user if they also want to add a `Dockerfile`. If the user says yes, review the example at `https://github.com/i-am-bee/agentstack-starter/blob/main/Dockerfile` and assemble a `Dockerfile` for the project. Do not force the use of `uv` if the project does not use it.
6. **Testing prompt:** Ask the user if they want to test the agent functionality. If they say yes, start the agent first in one terminal, and then use a separate terminal to run `agentstack run AGENT_NAME`. Do not attempt to interrupt the `run` command, as it may take a long time to complete. If the execution fails and an error is encountered, attempt to fix the error and run the test again. **Critically, do not create any new files or scripts (e.g., Python test scripts using pexpect) to perform this test. You must interact with the terminals directly.** Note that `agentstack run` triggers an interactive form; when testing programmatically via stdin, ensure you send precise literal newline characters to advance prompts.
7. **Run prompt:** Ask the user if they want to run the agent and be redirected to the Web UI. If the user agrees, start the agent and monitor the terminal for errors. If an error occurs, attempt to fix it and restart the agent.

---

## Verification Checklist (Required)

After wrapping, confirm:

### Code Quality

- [ ] Every `import` resolves to a real, installed module (run import validation)
- [ ] Agent function has a meaningful docstring (shown in UI)
- [ ] Agent handler is `async def` and uses `yield` for responses
- [ ] No `argparse` or `sys.argv` remains
- [ ] No business-logic changes unless explicitly approved (C1/C10)
- [ ] Temp files created at runtime are cleaned up (C3)

### Extensions & Config

- [ ] `yield AgentMessage(text=...)` used for all user-facing responses
- [ ] No env vars for API keys/model config — extensions used instead
- [ ] LLM config passed explicitly from extension, no fallback chains
- [ ] Optional extensions checked for presence/data before use (C13)
- [ ] Errors raise exceptions (Error extension), not yielded as `AgentMessage`
- [ ] No secrets logged, printed, or persisted (C14)

### Context & History

- [ ] `input` and `response` stored via `context.store()`
- [ ] `context_store=PlatformContextStore()` present if context is persisted/read
- [ ] Multi-turn uses `context.load_history()`; single-turn only if intentionally needed

### Forms & Files

- [ ] Single-turn with structured params → `initial_form` is defined (C8)
- [ ] Filesystem file inputs replaced with `FileField` form uploads (C20)
- [ ] Text-processing agents use broad MIME types with content-type branching and extraction
- [ ] No local filesystem reads for user-provided files

### Dependencies

- [ ] `agentstack-sdk~=<VERSION>` added to project's existing dependency file (C5)
- [ ] No Dockerfile unless explicitly requested (C2)

### Validation (must be performed live)

- [ ] Start the server, fetch `/.well-known/agent-card.json` — confirm HTTP 200 and valid JSON. **Show full output to the user.**
- [ ] Ask user if they want a `Dockerfile`
- [ ] Ask user if they want to test via `agentstack run AGENT_NAME` (no test scripts — use terminals directly)
