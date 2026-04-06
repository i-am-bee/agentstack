---
title: "GPT Researcher (LangGraph Agent) integration"
description: "How to integrate the agent written in LangGraph."
---

Integrating an agent written in any framework into AgentStack is straightforward. In this example, we will demonstrate how to integrate a [GPT-Researcher](https://github.com/assafelovic/gpt-researcher) agent built with LangGraph.

## Prerequisites

- AgentStack installed ([Quickstart](../introduction/quickstart))

## Agent Integration

<Steps>
<Step title="Clone the GPT Researcher repository">
```bash
git clone git@github.com:assafelovic/gpt-researcher.git
cd gpt-researcher
```
</Step>

<Step title="Add the agentstack-sdk dependency">
1. Open the `requirements.txt` file.
2. Add `agentstack-sdk>=0.5.2`.
3. Install the dependencies: `pip install -r requirements.txt`.
</Step>

<Step title="Use AgentStack SDK to start the agent">

Replace the code in the `main.py` file:

```python
# type: ignore
from backend.server.app import app

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

with the following:

```python
# type: ignore
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext
from agentstack_sdk.a2a.types import AgentMessage

server = Server()

@server.agent(
    name="GPT Researcher",
)
async def my_wrapped_agent(
    input: Message,
    context: RunContext
):
    user_message = get_message_text(input)

    researcher = GPTResearcher(
        query=user_message, report_type="research_report", verbose=True
    )

    await researcher.conduct_research()
    standard_report = await researcher.write_report()
    yield AgentMessage(text=str(standard_report))


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    run()
```
</Step>

<Step title="Run your agent">

In your terminal:

```bash
python main.py
```

Navigate to [http://localhost:8334](http://localhost:8334) to see your agent in the list.
</Step>

<Step title="Use AgentStack LLM">

Update `main.py` to use the provided LLM configuration:

```python
# type: ignore
from agentstack_sdk.a2a.extensions import (
    LLMServiceExtensionSpec,
    LLMServiceExtensionServer
)

async def my_wrapped_agent(
    input: Message,
    context: RunContext,
    llm: Annotated[
        LLMServiceExtensionServer,
        LLMServiceExtensionSpec.single_demand(
            suggested=(
                "watsonx:meta-llama/llama-3-3-70b-instruct",
                "watsonx:openai/gpt-oss-120b",
            )
        ),
    ],
):
    if llm and llm.data and llm.data.llm_fulfillments:
        # Get LLM configuration
        # Single demand is resolved to default (unless specified otherwise)
        llm_config = llm.data.llm_fulfillments.get("default")
        model = f"openai:{llm_config.api_model}"

        os.environ["OPENAI_API_KEY"] = llm_config.api_key
        os.environ["OPENAI_API_BASE"] = llm_config.api_base
        os.environ["FAST_LLM"] = model
        os.environ["SMART_LLM"] = model
        os.environ["STRATEGIC_LLM"] = model

```
</Step>

<Step title="Send Trajectory Data">

Update `main.py` to include trajectory metadata:

```python
# type: ignore
from agentstack_sdk.a2a.extensions import (
    LLMServiceExtensionSpec,
    LLMServiceExtensionServer,
    TrajectoryExtensionServer,
    TrajectoryExtensionSpec
)

async def my_wrapped_agent(
    input: Message,
    context: RunContext,
    trajectory: Annotated[TrajectoryExtensionServer, TrajectoryExtensionSpec()],
    llm: Annotated[
        LLMServiceExtensionServer,
        LLMServiceExtensionSpec.single_demand(
            suggested=(
                "watsonx:meta-llama/llama-3-3-70b-instruct",
                "watsonx:openai/gpt-oss-120b",
            )
        ),
    ],
):
    # ... previous configuration code ...

    class LogHandler:
        async def on_tool_start(self, tool_name, **kwargs):
            await context.yield_async(trajectory.trajectory_metadata(title=tool_name, content=str(kwargs)))
        
        async def on_agent_action(self, action, **kwargs):
            await context.yield_async(trajectory.trajectory_metadata(title=action, content=str(kwargs)))
        
        async def on_research_step(self, step, details):
            await context.yield_async(trajectory.trajectory_metadata(title=step, content=str(details)))
            
            
    # Initialize the researcher with the log handler
    researcher = GPTResearcher(
        query=user_message, report_type="research_report", verbose=True, log_handler=LogHandler()
    )
```
</Step>
</Steps>
