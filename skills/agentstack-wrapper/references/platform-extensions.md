# Platform Extensions Reference

Use this reference for selecting and implementing Agent Stack platform extensions.

## Extension Selection Matrix

| Extension             | Use when the Agent                                                                                       | Documentation                                                                                                                                                                                                                  |
| --------------------- | -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **LLM Proxy Service** | Needs platform-provided language model access and credentials                                            | [LLM Proxy Service](https://agentstack.beeai.dev/stable/agent-integration/llm-proxy-service.md)                                                                                                                                |
| **Forms**             | Requires structured, named parameter inputs (not just free text) as initial input or during conversation | [Collect Input with Forms](https://agentstack.beeai.dev/stable/agent-integration/forms.md)                                                                                                                                     |
| **Trajectory**        | Yields multi-step reasoning, tool calls, long-running progress, or explicit debugging traces             | [Visualize Agent Trajectories](https://agentstack.beeai.dev/stable/agent-integration/trajectory.md)                                                                                                                            |
| **Files**             | Needs to read image or document files uploaded by the user                                               | [Working with Files](https://agentstack.beeai.dev/stable/agent-integration/files.md)                                                                                                                                           |
| **Error**             | Needs to report structured, user-visible failures and stack traces                                       | [Handle Errors](https://agentstack.beeai.dev/stable/agent-integration/error.md)                                                                                                                                                |
| **Settings**          | Has configurable behavior (for example, "Thinking Mode")                                                 | [Configure Agent Settings](https://agentstack.beeai.dev/stable/agent-integration/agent-settings.md)                                                                                                                            |
| **OAuth**             | Accesses OAuth-protected third-party APIs (for example, GitHub or Slack)                                 | [OAuth](https://agentstack.beeai.dev/stable/agent-integration/oauth.md)                                                                                                                                                        |
| **MCP**               | Uses Model Context Protocol tools or servers                                                             | [MCP Integration](https://agentstack.beeai.dev/stable/agent-integration/mcp.md)                                                                                                                                                |
| **Embedding**         | Performs vector search or uses RAG strategies                                                            | [Build RAG Pipelines](https://agentstack.beeai.dev/stable/agent-integration/rag.md)                                                                                                                                            |
| **Approval**          | Performs sensitive tool calls requiring user consent                                                     | [Approve Tool Calls](https://agentstack.beeai.dev/stable/agent-integration/tool-calls.md)                                                                                                                                      |
| **Secrets**           | Needs user-provided API keys or tokens at runtime                                                        | [Manage Runtime Secrets](https://agentstack.beeai.dev/stable/agent-integration/secrets.md) (Note: Check `secrets.data` and use `request_secrets(params=...)` only through a declared `secrets` extension parameter if missing) |
| **Env Variables**     | Requires custom environment-level deployment configuration variables                                     | [Environment Variables](https://agentstack.beeai.dev/stable/agent-integration/env-variables.md)                                                                                                                                |
| **Canvas**            | Needs to edit artifacts or code selected by the user                                                     | [Work with Canvas](https://agentstack.beeai.dev/stable/agent-integration/canvas.md)                                                                                                                                            |
| **Citations**         | References documents or external URLs                                                                    | [Add Citations to Agent Responses](https://agentstack.beeai.dev/stable/agent-integration/citations.md)                                                                                                                         |

For a complete overview of all available extensions: **[Agent Integration Overview](https://agentstack.beeai.dev/stable/agent-integration/overview.md)**

## Configuration & Secret Guidance Location

For configuration variable mapping, secret handling, and related anti-patterns, use `references/configuration-variables.md`.

## Trajectory Guidance Location

For trajectory decision rules and implementation patterns, use `references/trajectory.md`.
