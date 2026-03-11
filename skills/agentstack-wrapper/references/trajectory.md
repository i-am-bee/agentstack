# Trajectory Reference

Use this reference for trajectory decision rules and implementation.

## Trajectory Output Rule

Use this decision rule:

- **Required:** yield trajectory for meaningful intermediate activity: multi-step execution, loops, tool calls, or progress updates. If the agent has multiple steps, it almost always needs trajectories.
- **Required (Logs/Prints):** if the original agent uses logging or `print` statements, these are prime candidates to be converted into trajectory entries.
- **Required (hidden internals):** if internal steps are not directly visible, yield trajectory at visible milestones: start, major phase change, completion, and failure.
- **Optional:** for simple single-step responders with no meaningful intermediate activity, trajectory may be omitted.
- **Default:** when uncertain, enable trajectory.

Trajectory entries are metadata for transparency and observability. They are not a substitute for the agent's user-facing response message.

## Trajectory Implementation

When implementing trajectories, follow the [Trajectory Documentation](https://agentstack.beeai.dev/stable/agent-integration/trajectory.md) and utilize these patterns:

- **Import**: `from agentstack_sdk.a2a.extensions import TrajectoryExtensionServer, TrajectoryExtensionSpec`
- **Injection**: `trajectory: Annotated[TrajectoryExtensionServer, TrajectoryExtensionSpec()]` as an agent function parameter.
- **`yield`**: Use `yield trajectory.trajectory_metadata(title="...", content="...")` within the main agent generator to emit progress updates.
- **`group_id` for updates**: Use `yield trajectory.trajectory_metadata(title="...", content="...", group_id="...")` to update an existing step instead of creating a new one.
- **Nested functions**: To emit trajectory entries from within nested asynchronous functions or utility methods where `yield` is not possible, you must pass the `trajectory` object and use `trajectory.trajectory_metadata(...)` but the final result must still be `yield`ed by the main generator.

## Anti-Patterns

- Never use `AgentMessage` with empty text to send trajectory metadata.
