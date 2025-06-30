import os
from textwrap import dedent
from typing import Any, AsyncIterator

import yaml
from acp_sdk import (
    MessagePart,
    Message,
    MessagePartEvent,
    GenericEvent,
    MessageCompletedEvent,
    Error,
    ErrorCode,
    Metadata,
    Link,
    LinkType,
)
from acp_sdk.client import Client
from acp_sdk.server import Server
from pydantic import Field, BaseModel, AnyUrl


class WorkflowStep(BaseModel):
    agent: str
    instruction: str


class StepsConfiguration(BaseModel):
    steps: list[WorkflowStep] = Field(min_length=1)


def format_agent_input(instruction: str, previous_output: dict[str, Any] | str) -> str:
    if not previous_output:
        return instruction
    return f"""{
        previous_output if isinstance(previous_output, str) else yaml.dump(previous_output, allow_unicode=True)
    }\n---\n{instruction}"""


def extract_messages(exc):
    if isinstance(exc, BaseExceptionGroup):
        return [(exc_type, msg) for e in exc.exceptions for exc_type, msg in extract_messages(e)]
    else:
        return [(type(exc).__name__, str(exc))]


server = Server()


@server.agent(
    metadata=Metadata(
        programming_language="Python",
        links=[
            Link(
                type=LinkType.SOURCE_CODE,
                url=AnyUrl(
                    f"https://github.com/i-am-bee/beeai-platform/blob/{os.getenv('RELEASE_VERSION', 'main')}"
                    "/agents/official/sequential-workflow"
                ),
            )
        ],
        license="Apache 2.0",
        framework="ACP",
        use_cases=[
            "**Complex Text Processing**: Ideal for tasks that require multiple stages of processing, such as summarization followed by sentiment analysis.",
            "**Automated Workflows**: Suitable for automated content processing pipelines that leverage multiple AI models.",
            "**Dynamic Instruction Handling**: Useful when dynamic instructions need to be provided to different agents based on prior processing results.",
        ],
        documentation=dedent(
            """\
            The sequential workflow agent is designed to manage and execute a series of text-processing tasks using multiple AI agents. It takes a series of steps, each specifying an agent and its corresponding instruction, and processes text data through these agents in a sequential manner. The agent ensures that each subsequent agent receives the output of the previous agent, formatted as YAML, along with its specific instruction, thus creating a seamless workflow for complex text-processing tasks.

            ## How It Works

            The agent receives an initial input text and a list of steps, each comprising an agent name and its instruction. It validates the availability and compatibility of the specified agents. The workflow proceeds by passing the formatted output of each agent as input to the next, adhering to the instructions specified for each step. This process continues until all steps are executed, and the final output is generated.

            ## Input Parameters (Message Parts)
            - **input** (text/plain) – The initial text input to be processed by the workflow.
            - **steps** (application/json) – A list of steps, each containing:
              - **agent** (str) – The name of the agent to execute.
              - **instruction** (str) – The specific instruction for the agent.

            ## Key Features
            - **Sequential Execution**: Manages the flow of data and instructions between multiple text-processing agents.
            - **YAML Formatting**: Uses YAML to format outputs for seamless interoperability between agents.
            - **Validation**: Ensures that each agent in the sequence is available and compatible with the expected input schema.
            - **Progress Reporting**: Provides detailed logs and progress updates throughout the workflow execution.
            """
        ),
    )
)
async def sequential_workflow(input: list[Message]) -> AsyncIterator:
    """
    The agent orchestrates a sequence of text-processing AI agents, managing the flow of information and instructions
    between them.
    """
    try:
        last_message = input[-1]
        step_part = [part for part in last_message.parts if part.content_type == "application/json"]
        if not step_part:
            raise ValueError("Missing steps configuration")
        steps = StepsConfiguration.model_validate_json(step_part[-1].content).steps
    except ValueError as ex:
        yield Error(code=ErrorCode.INVALID_INPUT, message=f"Missing or invalid steps configuration: {ex}")
        return

    base_url = f"{os.getenv('PLATFORM_URL', 'http://localhost:8333').rstrip('/')}/api/v1/acp"
    current_step = None

    try:
        async with Client(base_url=base_url) as client:
            server_agents_by_name = {agent.name: agent async for agent in client.agents()}
            if missing_agents := (set(step.agent for step in steps) - server_agents_by_name.keys()):
                yield Error(code=ErrorCode.INVALID_INPUT, message=f"The following agents are missing: {missing_agents}")
                return

            previous_output = None
            for idx, step in enumerate(steps):
                current_step = step

                yield {
                    "agent_name": step.agent,
                    "agent_idx": idx,
                    "message": f"✅ Agent {step.agent}[{idx}] started processing",
                }

                async for event in client.run_stream(
                    agent=step.agent,
                    input=[Message(parts=[MessagePart(content=format_agent_input(step.instruction, previous_output))])],
                ):
                    match event:
                        case MessagePartEvent(part=part):
                            yield part.model_copy(update={"agent_idx": idx, "agent_name": step.agent})
                        case GenericEvent(generic=generic):
                            yield generic.model_copy(update={"agent_idx": idx, "agent_name": step.agent})
                        case MessageCompletedEvent(message=message):
                            previous_output = str(message)
                            yield {
                                "agent_name": step.agent,
                                "agent_idx": idx,
                                "message": f"✅ Agent {step.agent}[{idx}] finished successfully",
                            }
        yield MessagePart(content=previous_output)
    except Exception as e:
        step_msg = f"{current_step.agent}[{idx}] - " if current_step else ""
        yield Error(code=ErrorCode.INVALID_INPUT, message=f"{step_msg}{extract_messages(e)}")


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    run()
