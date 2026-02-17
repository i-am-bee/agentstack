# LangGraph Reflection Agent

This agent uses LangGraph to implement a reflection loop for writing and improving essays.

## Features

- Essay generation based on user input.
- Critique generation for the essay.
- Iterative improvement through reflection.

## Development

Run locally:

```bash
uv run server
```

## Migration Guide: Wrapping Reflection Agent for AgentStack

Follow these steps to convert a standard LangGraph [reflection agent](https://github.com/langchain-ai/langgraph/blob/23961cff61a42b52525f3b20b4094d8d2fba1744/docs/docs/tutorials/reflection/reflection.ipynb) into an AgentStack-compatible microservice.

### Prerequisites

- [AgentStack SDK](https://agentstack.beeai.dev/stable/introduction/quickstart) installed.
- Understanding of the original `reflection.py` logic.

### Integration Process

#### 1. Initialize the Server

Instead of running top-level script logic, you need to wrap it in an AgentStack `Server`.

```python
from agentstack_sdk.server import Server
server = Server()
```

#### 2. Define Agent Metadata

Decorate your main agent function with `@server.agent()`. Provide a name, description, and UI details.

```python
from agentstack_sdk.a2a.extensions import AgentDetail

@server.agent(
    name="Reflection Agent",
    description="Reflection agent that writes essays and reflects on them",
    detail=AgentDetail(
        interaction_mode="multi-turn",
        user_greeting="Hello! I am your essay assistant. What would you like me to write about today?",
        input_placeholder="Enter your essay topic or request here...",
    ),
)
async def reflection_agent(input: Message, context: RunContext, ...):
    # logic goes here
```

#### 3. Request Platform Services

Use extensions to request an LLM and provide progress updates (trajectory). This replaces hardcoded model initializations.

```python
from typing import Annotated
from agentstack_sdk.a2a.extensions import (
    LLMServiceExtensionSpec,
    LLMServiceExtensionServer,
    TrajectoryExtensionServer,
    TrajectoryExtensionSpec,
)

# In the agent function arguments:
async def reflection_agent(
    input: Message,
    context: RunContext,
    trajectory: Annotated[TrajectoryExtensionServer, TrajectoryExtensionSpec()],
    llm_service: Annotated[
        LLMServiceExtensionServer,
        LLMServiceExtensionSpec.single_demand(suggested=("ollama:llama3.1:8b", "openai:gpt-4o"))
    ],
):
    # Resolve LLM config from fulfillment
    llm_config = llm_service.data.llm_fulfillments.get("default")
    llm = ChatOpenAI(
        model=llm_config.api_model,
        api_key=llm_config.api_key,
        base_url=llm_config.api_base,
    )
```

#### 4. Extract User Input

Convert the A2A `Message` into a standard string that LangGraph can use.

```python
from a2a.utils.message import get_message_text

user_input = get_message_text(input)
```

#### 5. Stream Graph Events to Trajectory

Instead of printing to console, use the `trajectory` extension to send updates back to the AgentStack UI.

```python
async for event in graph.astream({"messages": [HumanMessage(content=user_input)]}, config):
    for node_name, output in event.items():
        if "messages" in output:
            last_msg = output["messages"][-1]
            yield trajectory.trajectory_metadata(
                title=node_name,
                content=last_msg.content,
            )
```

#### 6. Finalize the Entry Point

Ensure the script runs the server using a `run()` function, allowing it to be managed by the platform.

```python
def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))

if __name__ == "__main__":
    run()
```
