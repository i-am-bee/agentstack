# Content Builder Agent (DeepAgents)

This project is an adapted implementation of the Content Builder Agent originally published in the
[DeepAgents repository](https://github.com/langchain-ai/deepagents/tree/master/examples/content-builder-agent).

The original example was designed to run in a stateful environment. This implementation
extends and modifies it to work reliably within the Agent Stack while supporting context persistence, parallels run and Agent Stack primitives like LLM Proxy Service, File Storage or Environment Variables.

## Implementation Notes

- **Custom Backend implementation**
  - Introduces a custom `Backend` to store generated files in the Agent Stack file storage rather than
    on the local filesystem.
  - Ensures files persist across multiple conversation turns.
  - Safely supports parallel executions where context is not shared.

- **File handling updates**
  - Updates the `generate_social_image` and `generate_cover` tools to store assets using the
    `File.create(...)` API provided by the Agent Stack instead of writing to disk.

- **Dynamic model loading**
  - Modifies the YAML loader to dynamically resolve and load the specified model using the
    LLM Fulfillment mechanism.

- **Message conversion utilities**
  - Adds helper functions to convert A2A messages into LangChain-compatible message formats.
