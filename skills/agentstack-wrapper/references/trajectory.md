# Trajectory Reference

Use this reference for trajectory decision rules and implementation.

## Trajectory Output Rule

Use this decision rule:

- **Required:** emit trajectory for meaningful intermediate activity: multi-step execution, loops, tool calls, or progress updates. If the agent has multiple steps, it almost always needs trajectories.
- **Required (Logs/Prints):** if the original agent uses logging or `print` statements, these are prime candidates to be converted into trajectory entries.
- **Required (hidden internals):** if internal steps are not directly visible, emit trajectory at visible milestones: start, major phase change, completion, and failure.
- **Optional:** for simple single-step responders with no meaningful intermediate activity, trajectory may be omitted.
- **Default:** when uncertain, enable trajectory.

Trajectory entries are metadata for transparency and observability. They are not a substitute for the agent's user-facing response message.

## Trajectory Implementation

When implementing trajectories, follow the [Trajectory Documentation](https://agentstack.beeai.dev/stable/agent-integration/trajectory.md) and utilize these patterns:

- **`yield`**: Use `yield trajectory.trajectory_metadata(title="", content="")` within the main agent generator to emit progress updates.
- **`context.yield_async() or context.yield_sync()`**: to emit trajectory entries from within nested asynchronous functions or utility methods, yielding an `AgentMessage` with trajectory metadata.
- **`trajectory_metadata`**: Use the `metadata` field of `AgentMessage` constructed via the extension's `trajectory_metadata()` method to provide structured, machine-readable context for each trajectory step.

## Anti-Patterns

- Never use `AgentMessage` with empty text to send trajectory metadata
