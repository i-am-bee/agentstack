# Wrapper & Entrypoint Reference (Step 4)

Use this reference for wrapper creation and server entrypoint implementation.

Create a new file (e.g., `agent.py`) with wrapping code, adapting original inputs without altering core business logic. Prefer additive files and minimal adapters. Preserve legacy HTTP contract endpoints if asserted by tests.

Follow the wrapping pattern from the official guide: **[Wrap Your Existing Agents](https://agentstack.beeai.dev/stable/deploy-agents/wrap-existing-agents.md)**

For building agents from scratch or understanding the full server pattern: **[Build New Agents](https://agentstack.beeai.dev/stable/deploy-agents/building-agents.md)**

Real-world examples of wrapped agents are available at: **[agents/ on GitHub](https://github.com/i-am-bee/agentstack/tree/main/agents)**

## Metadata Extraction

Before writing the code, analyze the original source (docstrings, CLI help, README) to populate the `@server.agent()` parameters:

- **Identity**: Set a user-friendly `name` and `version`.
- **Documentation**: Use `documentation_url` pointing to the source.
- **Detail**: Populate `AgentDetail` with `interaction_mode` (Step 2), `tools`, `author` (must be a dictionary, e.g., `{"name": "agentstack"}`), and `programming_language`.
- **Skills**: Define `AgentSkill` entries with `id`, `name`, `description`, `tags`, and `examples`.
- **Function Docstring**: The wrapper function's docstring should be a concise summary shown in registries.
- **Extensions**: Identify if the agent needs optional platform capabilities (Step 8) like Citations, Secrets, or Trajectory.

## Key Elements

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

## Implementation: Conditional Workflows

Based on the classification in Step 2, follow exactly ONE of these workflows:

### If the agent is Single-turn

```
- [ ] Extract user message with `get_message_text(input)`
- [ ] Only call `context.load_history()` if continuity is intentionally required
- [ ] Pass necessary inputs (from forms or text) to original agent logic
- [ ] Emit trajectory for meaningful intermediate activity (same rule as all agents)
- [ ] Yield the final response via `AgentMessage(text=result)`
- [ ] Persist both input and response via `context.store()`
```

### If the agent is Multi-turn

```
- [ ] Store input: Save incoming user message immediately with `await context.store(input)`
- [ ] Load history: Retrieve past conversation via `[msg async for msg in context.load_history() if isinstance(msg, Message)]`
- [ ] Execute agent: Pass the filtered history to the original agent logic
- [ ] Emit trajectory for meaningful intermediate activity (same rule as all agents)
- [ ] Yield response: Return final answering chunks with `yield AgentMessage(text=...)`
- [ ] Store response: Save the final response with `await context.store(response)`
```

## Entrypoint

Create a `run()` / `serve()` function protected by an `if __name__ == "__main__":` guard. This function should call `server.run()`:

- The server should be configured to listen on a `host` and `port` from environment variables (e.g., `host=os.getenv("HOST", "127.0.0.1")`, `port=int(os.getenv("PORT", 8000))`).
- If the agent persists or reads context history, you must pass `context_store=PlatformContextStore()` to `server.run()`.
- **Remove all CLI argument parsing** (`argparse`). Map required CLI inputs to the wrapper parameters instead (e.g., from Forms, Settings, or Environment variables).
- Only `auth_backend` if explicitly requested.
