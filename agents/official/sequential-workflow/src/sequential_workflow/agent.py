# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from textwrap import dedent
from typing import Any, AsyncIterator
import uuid

from a2a.client import A2AClient
from a2a.types import (
    AgentCard,
    AgentSkill,
    Artifact,
    DataPart,
    Message,
    MessageSendParams,
    Role,
    SendStreamingMessageRequest,
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
    TextPart,
    Part,
    TaskStatus,
    SendStreamingMessageSuccessResponse,
    JSONRPCErrorResponse,
    TaskState,
)
import yaml
from pydantic import Field, BaseModel

from beeai_sdk.a2a.extensions import AgentDetail
from beeai_sdk.server import Server


class WorkflowStep(BaseModel):
    provider_id: str
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
    documentation_url=(
        f"https://github.com/i-am-bee/beeai-platform/blob/{os.getenv('RELEASE_VERSION', 'main')}"
        "/agents/official/sequential-workflow"
    ),
    detail=AgentDetail(
        license="Apache 2.0",
        framework="ACP",
        ui_type="playground",
        use_cases=[
            "**Complex Text Processing**: Ideal for tasks that require multiple stages of processing, such as summarization followed by sentiment analysis.",
            "**Automated Workflows**: Suitable for automated content processing pipelines that leverage multiple AI models.",
            "**Dynamic Instruction Handling**: Useful when dynamic instructions need to be provided to different agents based on prior processing results.",
        ],
    ),
    skills=[
        AgentSkill(
            id="sequential_workflow",
            name="Sequential Workflow",
            tags=["workflow"],
            description=dedent(
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
    ],
)
async def sequential_workflow(steps_message: Message) -> AsyncIterator:
    """
    The agent orchestrates a sequence of text-processing AI agents, managing the flow of information and instructions
    between them.
    """
    try:
        if not steps_message.parts or not isinstance(steps_message.parts[0].root, DataPart):
            raise ValueError("Missing steps configuration")
        steps = StepsConfiguration.model_validate(steps_message.parts[0].root.data).steps
    except ValueError as ex:
        raise ValueError(f"Missing or invalid steps configuration: {ex}") from ex

    base_url = f"{os.getenv('PLATFORM_URL', 'http://localhost:8333').rstrip('/')}/api/v1/"
    current_step = None
    import httpx

    async with httpx.AsyncClient(base_url=base_url) as client:
        providers = await client.get("providers")
        providers.raise_for_status()
        providers_by_id = {p["id"]: p for p in providers.json()["items"]}
        if missing_providers := ({step.provider_id for step in steps} - providers_by_id.keys()):
            raise ValueError(f"The following providers are missing in the platform: {missing_providers}")

    agent_name = ""
    idx = 0
    try:
        previous_output = ""
        for idx, step in enumerate(steps):
            current_step = step
            async with httpx.AsyncClient() as http_client:
                agent_card = AgentCard.model_validate(providers_by_id[step.provider_id]["agent_card"])
                client = A2AClient(httpx_client=http_client, agent_card=agent_card)
                agent_name = agent_card.name

                yield {
                    "agent_name": agent_name,
                    "provider_id": step.provider_id,
                    "agent_idx": idx,
                    "message": f"✅ Agent {agent_name}[{idx}] started processing",
                }

                message = Message(
                    role=Role.user,
                    message_id=str(uuid.uuid4()),
                    parts=[Part(root=TextPart(text=format_agent_input(step.instruction, previous_output)))],
                )
                previous_output = ""
                async for event in client.send_message_streaming(
                    SendStreamingMessageRequest(id=str(uuid.uuid4()), params=MessageSendParams(message=message)),
                ):
                    match event.root:
                        case SendStreamingMessageSuccessResponse(
                            result=TaskStatusUpdateEvent(
                                status=TaskStatus(message=Message(parts=parts, metadata=metadata))
                            )
                            | TaskArtifactUpdateEvent(artifact=Artifact(parts=parts, metadata=metadata))
                        ):
                            for part in parts:
                                match part.root:
                                    case TextPart(text=text):
                                        previous_output += text
                                    case DataPart(data=data):
                                        previous_output += yaml.dump(data, allow_unicode=True)
                            yield event.root.result
                        case SendStreamingMessageSuccessResponse(
                            result=TaskStatusUpdateEvent(status=TaskStatus(state=TaskState.failed, message=message))
                        ):
                            parts = message.parts if message else []
                            text_part = [part.root for part in parts if isinstance(part.root, TextPart)]
                            raise RuntimeError(text_part[0].text if text_part else "Unknown error")

                        case JSONRPCErrorResponse(error=error):
                            raise RuntimeError(error.message)
                yield {
                    "provider_id": step.provider_id,
                    "agent_name": agent_name,
                    "agent_idx": idx,
                    "message": f"✅ Agent {agent_name}[{idx}] finished successfully",
                }
        yield previous_output
    except Exception as e:
        step_msg = f"{agent_name}[{idx}] - " if current_step else ""
        raise RuntimeError(f"{step_msg}{extract_messages(e)}")


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    run()
