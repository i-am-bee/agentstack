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
- [Step 8 – Configuration Variables & Secrets](#step-8--configuration-variables--secrets)
- [Step 9 – Agent Output](#step-9--output)
- [Step 10 – Use Platform Extensions](#step-10--use-platform-extensions)
- [Step 11 – Update README](#step-11--update-readme)
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
- If installing anything via `pip`, always use the `-qq` flag to suppress unnecessary output.

## Constraints (must follow)

| ID  | Rule                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| C1  | **No business-logic changes.** Only modify code for Agent Stack compatibility.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| C2  | **Strict minimal changes.** Do not add auth, Dockerfile (containerization is optional and separate), telemetry, or platform middleware unless explicitly requested. If an agent works with simple text, don't force a Form. If it works with env vars, refactor minimally.                                                                                                                                                                                                                                                                                                                                                                      |
| C3  | **Cleanup temp files.** If the agent downloads or creates helper files at runtime, add a cleanup step before the function returns.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| C4  | **Prioritize Public Access (No redundant tokens).** Only use the Secrets extension if the secret is strictly mandatory for the agent's core functionality and no public/anonymous access is viable. Do not add secrets or tokens that increase configuration burden if they were optional in the original agent (e.g., optional GitHub token). Preserve existing optional auth behavior unless removal is explicitly approved and documented as a behavior change. API keys must be passed explicitly, never read from env vars. For required third-party API credentials, Secrets or Env Variables extension is mandatory in the wrapped path. |
| C5  | **Detect existing tooling.** If the project uses `requirements.txt`, add `agentstack-sdk~=<VERSION>` there. If it uses `pyproject.toml`, add it there. Add `a2a-sdk` only when the project manages it directly, and keep it compatible with the chosen `agentstack-sdk` version. Never force `uv` or create duplicate manifests.                                                                                                                                                                                                                                                                                                                |
| C6  | **Package-First Source of Truth for Imports.** The **Inline Package Search** script defined in `references/dependencies.md` holds absolute priority for discovering correct import paths, class names, and types. You MUST run this script to map imports before relying on local reference files or online documentation. Do not guess imports or follow documented paths blindly if they conflict with the installed package.                                                                                                                                                                                                                 |
| C7  | **Documentation-Secondary Authority.** Local skill files in the `references/` folder and online documentation are the primary authority for _behavior, logic, and choice of extensions_, but they are secondary to package introspection for _exact implementation details_ like import paths.                                                                                                                                                                                                                                                                                                                                                  |
| C8  | **Fallback and Validation Order.** Use local source inspection and package introspection first for imports. Keep runtime/package verification as a final validation step after implementation.                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| C9  | **Structured Parameters to Forms.** For single-turn agents with named parameters, map them to an `initial_form` using `FormServiceExtensionSpec.demand(initial_form=...)`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| C10 | **Remove CLI arguments.** Remove all `argparse` or `sys.argv` logic. Replace mandatory CLI inputs with `initial_form` items, AgentStack Settings Extension (for runtime options), or AgentStack Env Variables.                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| C11 | **Approval gate for business-logic changes.** If compatibility requires business-logic changes, stop and request explicit approval with justification before proceeding.                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| C12 | **Preserve original helpers.** Do not delete original business-logic helpers unless strictly required. If removal is necessary, document why.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| C13 | **Optional extension safety.** Service/UI extensions are optional. Check presence/data before use (e.g., `if llm and llm.data ...`).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| C14 | **No secret exposure.** Never log, print, persist, or echo secret values (API keys, tokens, passwords). Redact sensitive values in logs and errors.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| C15 | **Complete Secret Integration.** Every secret variable requested via the Secrets extension (e.g., via `SecretDemand` or `request_secrets`) MUST be used in the agent's code or passed to the underlying framework. Do not request unused credentials.                                                                                                                                                                                                                                                                                                                                                                                           |
| C16 | **No remote script execution.** Never run untrusted remote code during wrapping. Use project manifests and trusted package metadata only.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| C17 | **Constrained outbound targets.** Do not introduce arbitrary network targets. Limit external calls to trusted dependency sources and runtime endpoints explicitly required by the wrapped agent contract.                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| C18 | **No dynamic command execution from input.** Do not introduce wrapper patterns that execute shell commands from user/model input (for example, `eval`, `exec`, `os.system`, or unsanitized `subprocess` calls).                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| C19 | **Read Wrapper Documentation First.** Before starting any implementation, you must read the official guide: [Wrap Your Existing Agents](https://agentstack.beeai.dev/stable/deploy-agents/wrap-existing-agents.md).                                                                                                                                                                                                                                                                                                                                                                                                                             |
| C20 | **Read Extension Documentation.** Before implementing any extension (Forms, LLM, Error, etc.), you **MUST** read its corresponding documentation URL (listed in Step 10) and extract the exact imports, class names, method names, properties, and their exact types directly from the official documentation. Do not guess these values. Only modify the agent code after reading the documentation.                                                                                                                                                                                                                                           |
| C21 | **Replace filesystem file inputs with platform file uploads.** If the original agent reads files from the local filesystem (e.g., `open()`, `pathlib.Path`, CLI file path arguments), replace those inputs with `FileField` form uploads and the platform `File` API. Do not assume local filesystem access at runtime. See Step 7b.                                                                                                                                                                                                                                                                                                            |
| C22 | **Context & Memory Optimization.** Do not attempt the entire transformation in one tool call. Follow the checklist iteratively. Use the built-in task/todo tracking tool (e.g., `manage_todo_list`) to track progress through the Integration Workflow Checklist — do not create separate markdown tracking files. Do not paste massive stack traces into the chat; extract only the relevant error.                                                                                                                                                                                                                                            |

---

## Context & Memory Optimization

To ensure the highest success rate and prevent AI context window exhaustion during complex transformations:

1. **Iterative Progress**: Execute the [Integration Workflow Checklist](#integration-workflow-checklist) strictly step-by-step. Use the built-in task/todo tracking tool to mirror the checklist items and mark them off as you complete each step. This provides visible progress tracking without creating extra files.
2. **Minimize Terminal Output**: When debugging, prevent massive stack traces from polluting the context. Extract specifically the `Exception` line and the immediate traceback file, omitting massive framework logs.
3. **Targeted Code Reading**: Do not repeatedly load massive files like `SKILL.md` or large source code files if they haven't changed.
4. **Do NOT create tracking files**: Do not create `task.md`, `implementation_plan.md`, `walkthrough.md`, or similar markdown artifacts for progress tracking. The built-in task tracking tool is the single source of progress state.

## Source-of-Truth Precedence (Required)

For every wrapping task, use this exact precedence order:

1. **Absolute Primary (highest priority):** Installed package/runtime introspection (the **Inline Package Search** in `references/dependencies.md`) for all imports, class names, and types.
2. **Primary (required second):** Local skill-provided files in the `references/` folder for architectural patterns, extension choices, and mapping logic.
3. **Secondary:** Official documentation URLs linked by this skill for detailed API behavior.
4. **Tertiary:** Local project source code and repository docs (README/AGENTS) to map behavior and integration points.
5. **Final step:** Runtime verification (imports/server checks) after implementation is complete.

If you use step 3, explicitly record what was missing from docs and why fallback was necessary.

**CRITICAL WORKFLOW REQUIREMENT:** For _every_ extension you decide to use (whether from LLM/Forms/Error steps or Platform Extensions), you MUST follow these exact steps in order:

1. Decide if the extension should be implemented.
2. If yes, **READ the documentation URL provided in the extension table below** (e.g., using a tool to read the webpage). This is mandatory and happens before any code edits.
3. Extract the correct imports, class names, method names, properties, and their exact types directly from the official documentation.
4. **Only AFTER reading the documentation**, proceed to write or modify the agent code. Never guess imports or rely on outdated memory.
5. If docs are incomplete/unclear, use local/runtime introspection as fallback and note the specific gap.

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
- [ ] Step 5a: Set suggested model to match the model used in the original agent
- [ ] Step 6: Implement Error Handling (requires reading docs)
- [ ] Step 7: Map Forms (if applicable) (requires reading docs)
- [ ] Step 7b: Adapt File Inputs (if applicable) (requires reading docs)
- [ ] Step 8: Map Configuration Variables & Secrets (requires reading docs)
- [ ] Step 8a: Credential audit completed (every external API credential source identified; required credentials mapped to Secrets extension)
- [ ] Step 9: Agent Output (requires reading docs)
- [ ] Step 10: Use Platform Extensions (requires reading docs for each chosen extension)
- [ ] Step 11: Update README
- [ ] Finalization Report (required)
- [ ] Verification Checklist (required)

```

**STOP GATE:** After Step 11, you MUST complete the Finalization Report and walk through every item in the Verification Checklist before reporting completion. The task is NOT done until both are finished.

## Readiness Check (before Step 1)

- [ ] A supported Python interpreter is selected in the active environment (Python >=3.12 and <3.14; not merely installed).
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

Read the agent's code and classify it. This determines the `interaction_mode` value:

| interaction_mode | Pattern                    | Indicators                                                                                                              |
| ---------------- | -------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| **single-turn**  | One request → one response | CLI entrypoint, `argparse` (must be removed), primarily stateless business logic, context persistence still recommended |
| **multi-turn**   | Conversation with memory   | Chat loop, message history, session state, memory object                                                                |

This classification determines:

- How to use `context.store()` and `context.load_history()`: persist input/response by default for all agents; `context.load_history()` is required for multi-turn, and optional for single-turn (use only when prior context is intentionally part of behavior)
- Whether to define an `initial_form` for structured inputs (single-turn with named parameters)

---

## Step 3 – Add and Install Dependencies

**Read [references/dependencies.md](references/dependencies.md) and follow it completely for Step 3.**

---

## Step 4 – Create the Server Wrapper & Entrypoint

**Read [references/wrapper-entrypoint.md](references/wrapper-entrypoint.md) and follow it completely for Step 4.**

---

## Step 5 – Wire LLM / Services via Extensions

**Read [references/llm-services.md](references/llm-services.md) and follow it completely for Step 5.**

Set the `suggested` model in `LLMServiceExtensionSpec.single_demand()` to the same model used in the original agent.

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

**Read [references/forms.md](references/forms.md) for the full implementation guide** (field types, Pydantic model, mid-conversation input).

---

## Step 7b – Adapt File Inputs

If the original agent reads files from the local filesystem or accepts file paths as CLI/function arguments, those inputs must be replaced with platform file uploads. Local filesystem access is not available at runtime. Even if the file contains plain text, still use a `FileField` upload — do not flatten file inputs into message text.

**Read [references/files.md](references/files.md) for detection patterns, replacement steps, text extraction, and mid-conversation uploads.**

---

## Step 8 – Configuration Variables & Secrets

**Read [references/configuration-variables.md](references/configuration-variables.md) and follow it completely for configuration mapping, secret handling, and anti-patterns.**

---

## Step 9 – Agent Output

### Trajectory Output Rule and Implementation

**Read [references/trajectory.md](references/trajectory.md) and follow it completely for trajectory decision rules and implementation.**

### Final Output Rule

The primary, final output returned to the user from the agent or LLM must **always** be emitted as a normal `AgentMessage` or `AgentArtifact`.

Trajectory should only contain the intermediate context, reasoning, and steps behind that final answer, but it is not a substitute for the final response.

If callbacks are sync-only, capture callback data and emit it later from the main agent handler.

### Artifact Output Rule

If the original agent generates, processes, or outputs **files** (such as CSVs, PDFs, images, or structured data dumps) as part of its execution, you **must** return those files to the caller as an `AgentArtifact`. Do not just write the file to the local disk and yield a text message saying "File generated", as local filesystem changes are not returned to the platform UI.

Use the platform's API to construct an `AgentArtifact` pointing to the generated content. For specific implementation details, refer to the [AgentArtifact Documentation](https://agentstack.beeai.dev/stable/agent-integration/messages#agentartifact).

---

## Step 10 – Use Platform Extensions

Enhance the agent with platform-level capabilities by injecting extensions via `Annotated` function parameters.

**Read [references/platform-extensions.md](references/platform-extensions.md) for extension selection and documentation links.**

Treat this reference as required input for Step 10 decisions and implementation.

---

## Step 11 – Update README

Update the project's `README.md` (or create one if missing) with instructions on how to run the wrapped agent server. Include:

1. **Install dependencies** using the project's existing tooling (e.g. `uv pip install -qq -r requirements.txt` or `pip install -qq -r requirements.txt`). Make sure to use the `-qq` flag to keep the terminal output clean.
2. **Environment Configuration** — Document required `.env` patterns if `python-dotenv` is used. However, ensure the agent still receives configuration explicitly instead of reading env arguments internally.
3. **Run the server** with the appropriate command (e.g. `uv run server.py` or `python server.py`).
4. **Default address** — mention that the server starts at `http://127.0.0.1:8000` by default and can be configured via `HOST` and `PORT` environment variables.

Remove or replace any outdated CLI usage examples (e.g. `argparse`-based commands) that no longer apply after wrapping.

---

## Anti-Patterns

When building and testing the wrapper, ensure you avoid these common pitfalls:

- **Never access `.text` directly on a `Message` object.** Message content is multipart. Always use `get_message_text(input)` (requires `from a2a.utils.message import get_message_text`).
- **Never save files to local disk.** AgentStack environments are ephemeral. All generated files should be instantiated directly in memory and yielded as `AgentArtifact(parts=[file.to_file_part()])`. See [Manage Files](https://agentstack.beeai.dev/stable/agent-integration/files.md) for the correct `File.create()` API usage.
- **Never use synchronous functions for the agent handler.** Agent functions must be `async def` generators using `yield`.
- **Never hide platform wiring behind abstraction layers.** Keep `@server.agent(...)`, extension parameters, and integration contracts visible in the main entrypoint so behavior is auditable.
- **Never treat runtime inspection as first source.** `agentstack_sdk` and `a2a` details must come from provided docs first; use installed-environment inspection only as documented fallback, then validate imports at the end.
- **Never assume history is auto-saved.** Explicitly call `await context.store(input)` and `await context.store(response)`.
- **Never assume persistent history without `PlatformContextStore`.** Without it, context storage is in-memory and lost on restart.
- **Never forget to filter history.** `context.load_history()` returns Messages and Artifacts. Filter with `isinstance(message, Message)`.
- **Never store individual streaming chunks.** Accumulate the full response and store once.
- **Never treat extension data as dictionaries.** Use dot notation (e.g., `config.api_key`, not `config.get("api_key")`).
- **Never use `llm_config.identifier` as the model name.** Use `llm_config.api_model` instead.
- **Never assume all extension specs have `.demand()`.** Some use `.single_demand()` or direct instantiation. Always verify.
- **Never assume secrets are pre-configured or immediately present in `secret_fulfillments`.** Even if requested via `single_demand()`, you must explicitly poll for them using `await secrets.request_secrets(params=SecretsServiceExtensionParams(...))` if they are missing at runtime.
- **Never call `emit()` synchronously on the trajectory extension.** The `TrajectoryExtensionServer` does not support `.emit()`. You must explicitly output trajectory steps by yielding them: `yield trajectory.trajectory_metadata(title="...", content="...")`.
- **Never silently remove existing optional auth paths.** If the source agent supported optional tokens/keys, preserve that optional behavior unless an approved behavior change is explicitly documented.
- **Never use Forms for a single free-form follow-up.** Use A2A `input-required` for one-question free text prompts; reserve Forms for structured multi-field input.
- **Never mismatch form field IDs and model fields.** Mismatched IDs cause silent parse failures.
- **Never use `context.session_id`.** The `RunContext` object uses `context.context_id` for session identification.
- **Never guess platform object attributes.** `FormRender` uses `fields` (not `items`), `TextField` uses `label` (not `title`).
- **Never skip null-path handling for forms.** Handle `None` for cancelled or unsubmitted forms.
- **Never use `parse_initial_form(...)` truthiness to route turns in multi-turn agents.** Route by presence/absence of persisted session state from `context.load_history()`.
- **Never assume uploaded file URIs are HTTP URLs.** Parse `agentstack://` URIs with `PlatformFileUrl`.
- **Never skip extraction polling.** `create_extraction()` is async — poll `get_extraction()` until `status == 'completed'`.

## Failure Conditions

- If fresh docs cannot be fetched, stop and report that execution cannot continue without current docs.
- If required details are missing from docs and no reliable fallback source is available, stop and report the blocker explicitly.

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
- [ ] No business-logic changes unless explicitly approved (C1/C11)
- [ ] Temp files created at runtime are cleaned up (C3)

### Extensions & Config

- [ ] `yield AgentMessage(text=...)` used for all user-facing responses
- [ ] No env vars for API keys/model config — extensions used instead
- [ ] Required external API tools (e.g., Tavily) obtain credentials via Secrets extension and pass them explicitly to constructors/clients
- [ ] Every secret requested via the Secrets extension is actually used in the code or passed to the underlying service (C15)
- [ ] LLM config passed explicitly from extension, no fallback chains
- [ ] Optional extensions checked for presence/data before use (C13)
- [ ] Errors raise exceptions (Error extension), not yielded as `AgentMessage`
- [ ] No secrets logged, printed, or persisted (C14)

### Context & History

- [ ] `input` and `response` stored via `context.store()`
- [ ] `context_store=PlatformContextStore()` present if context is persisted/read
- [ ] Multi-turn uses `context.load_history()`; single-turn only if intentionally needed

### Forms & Files

- [ ] Single-turn with structured params → `initial_form` is defined (C9)
- [ ] Filesystem file inputs replaced with `FileField` form uploads (C21)
- [ ] Text-processing agents use broad MIME types with content-type branching and extraction
- [ ] No local filesystem reads for user-provided files

### Dependencies

- [ ] `agentstack-sdk~=<VERSION>` added to project's existing dependency file (C5)
- [ ] No Dockerfile unless explicitly requested (C2)

### Validation (must be performed live)

- [ ] Start the server, fetch `/.well-known/agent-card.json` — confirm HTTP 200 and valid JSON. **Show full output to the user.**
- [ ] Ask user if they want a `Dockerfile`
- [ ] Ask user if they want to test via `agentstack run AGENT_NAME` (no test scripts — use terminals directly) and listen for errors. If errors occur, fix and retest until successful. Inform the user very briefly, that then they can ask you to check out terminal output, if errors occur, and you will attempt to fix them.
