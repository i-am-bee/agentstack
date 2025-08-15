# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections import defaultdict
import logging
from typing import Annotated
import os
import uuid

from a2a.types import AgentSkill, Artifact, FilePart, FileWithUri, Message, Part
from beeai_framework.adapters.openai import OpenAIChatModel
from beeai_framework.agents.experimental import RequirementAgent

from beeai_framework.backend import ChatModelParameters
from beeai_framework.emitter import EmitterOptions
from beeai_framework.memory import UnconstrainedMemory
from beeai_framework.middleware.trajectory import GlobalTrajectoryMiddleware
from beeai_framework.tools import Tool
from beeai_sdk.a2a.extensions import (
    AgentDetail,
    CitationExtensionServer,
    CitationExtensionSpec,
    TrajectoryExtensionServer,
    TrajectoryExtensionSpec,
)
from beeai_framework.agents.experimental.utils._tool import FinalAnswerTool
from beeai_sdk.a2a.types import AgentMessage
from beeai_sdk.server import Server
from beeai_sdk.server.context import Context
from openinference.instrumentation.beeai import BeeAIInstrumentor
from rag.helpers.citations import extract_citations
from rag.helpers.platform import ApiClient, get_file_url
from rag.helpers.trajectory import ToolCallTrajectoryEvent
from rag.helpers.event_binder import EventBinder
from rag.helpers.vectore_store import (
    create_vector_store,
    embed_all_files,
    CreateVectorStoreEvent,
)
from rag.tools.files.file_creator import FileCreatorToolOutput
from rag.tools.files.utils import FrameworkMessage, extract_files, to_framework_message
from rag.tools.files.vector_search import VectorSearchTool
from rag.tools.general.act import (
    ActAlwaysFirstRequirement,
    ActTool,
    act_tool_middleware,
)
from rag.tools.general.clarification import (
    ClarificationTool,
    clarification_tool_middleware,
)
from rag.tools.general.current_time import CurrentTimeTool


BeeAIInstrumentor().instrument()
## TODO: https://github.com/phoenixframework/phoenix/issues/6224
logging.getLogger("opentelemetry.exporter.otlp.proto.http._log_exporter").setLevel(
    logging.CRITICAL
)
logging.getLogger("opentelemetry.exporter.otlp.proto.http.metric_exporter").setLevel(
    logging.CRITICAL
)

logger = logging.getLogger(__name__)

messages: defaultdict[str, list[Message]] = defaultdict(list)
framework_messages: defaultdict[str, list[FrameworkMessage]] = defaultdict(list)
vector_store_id: str | None = None  # TODO: Implement vector store ID management

server = Server()


@server.agent(
    name="RAG",
    documentation_url=(
        f"https://github.com/i-am-bee/beeai-platform/blob/{os.getenv('RELEASE_VERSION', 'main')}"
        "/agents/official/beeai-framework/rag"
    ),
    version="1.0.0",
    default_input_modes=["text/plain", "application/pdf"],
    default_output_modes=["text/plain"],
    detail=AgentDetail(
        ui_type="chat",
        user_greeting="What would you like to read?",
        tools=[],
        framework="BeeAI",
    ),
    skills=[
        AgentSkill(
            id="rag",
            name="RAG Agent",
            description="A Retrieval-Augmented Generation (RAG) agent that retrieves and generates text based on user queries.",
            tags=["RAG", "retrieval", "generation"],
        )
    ],
)
async def rag(
    message: Message,
    context: Context,
    trajectory: Annotated[TrajectoryExtensionServer, TrajectoryExtensionSpec()],
    citation: Annotated[CitationExtensionServer, CitationExtensionSpec()],
):

    extracted_files = await extract_files(
        history=messages[context.context_id], incoming_message=message
    )
    input = to_framework_message(message)

    FinalAnswerTool.description = """Assemble and send the final answer to the user. When using information gathered from other tools that provided URL addresses, you MUST properly cite them using markdown citation format: [description](URL).

# Citation Requirements:
- Use descriptive text that summarizes the source content
- Include the exact URL provided by the tool
- Place citations inline where the information is referenced

# Examples:
- According to [OpenAI's latest announcement](https://example.com/gpt5), GPT-5 will be released next year.
- Recent studies show [AI adoption has increased by 67%](https://example.com/ai-study) in enterprise environments.
- Weather data indicates [temperatures will reach 25°C tomorrow](https://weather.example.com/forecast)."""  # type: ignore

    tools = [
        # Auxiliary tools
        ActTool(),  # Enforces correct thinking sequence by requiring tool selection before execution
        ClarificationTool(),  # Allows agent to ask clarifying questions when user requirements are unclear
        CurrentTimeTool(),
    ]

    if extracted_files:
        async with ApiClient() as client:
            global vector_store_id
            if vector_store_id is None:
                start_event = CreateVectorStoreEvent(phase="start")
                yield start_event.metadata(trajectory)
                vector_store_id = await create_vector_store(client)
                yield CreateVectorStoreEvent(
                    vector_store_id=vector_store_id,
                    parent_id=start_event.id,
                    phase="end",
                ).metadata(trajectory)

            tools.append(VectorSearchTool(vector_store_id=vector_store_id))
            async for item in embed_all_files(
                client,
                all_files=extracted_files,
                vector_store_id=vector_store_id,
                trajectory=trajectory,
            ):
                yield item

    requirements = [
        ActAlwaysFirstRequirement(),  #  Enforces the ActTool to be used before any other tool execution.
    ]

    llm = OpenAIChatModel(
        model_id=os.getenv("LLM_MODEL", "llama3.1"),
        api_key=os.getenv("LLM_API_KEY", "dummy"),
        base_url=os.getenv("LLM_API_BASE", "http://localhost:11434/v1"),
        parameters=ChatModelParameters(temperature=0.0),
        tool_choice_support=set(),
    )

    # Create agent
    agent = RequirementAgent(
        llm=llm,
        tools=tools,
        memory=UnconstrainedMemory(),
        requirements=requirements,
        middlewares=[
            GlobalTrajectoryMiddleware(included=[Tool]),  # ChatModel,
            act_tool_middleware,
            clarification_tool_middleware,
        ],
    )

    messages[context.context_id].append(message)
    framework_messages[context.context_id].append(input)

    await agent.memory.add_many(framework_messages[context.context_id])
    final_answer = None
    event_binder = EventBinder()

async def handle_tool_start(event, meta):
        print(f"Handle tool start")
        # Store the start event ID using EventBinder
        event_binder.set_start_event_id(meta)

        event_id = event_binder.get_event_id(meta)
        print(f"event_id: {event_id}")
        print(f"meta.trace.id: {meta.trace.id}")
        tool_start_event = ToolCallTrajectoryEvent(
            id=event_id,
            kind=meta.creator.name,
            phase="start",
            input=event.input,
            output=None,
            error=None,
        )
        await context.yield_async(tool_start_event.metadata(trajectory))

    async def handle_tool_success(event, meta):
        print(f"Handle tool success")
        # Get the corresponding start event ID using EventBinder
        start_event_id = event_binder.get_start_event_id(meta)

        event_id = event_binder.get_event_id(meta)
        print(f"event_id: {event_id}")
        print(f"start_event_id: {start_event_id}")
        print(f"meta.trace.id: {meta.trace.id}")
        tool_end_event = ToolCallTrajectoryEvent(
            kind=meta.creator.name,
            phase="end",
            parent_id=start_event_id,  # Use the start event ID from EventBinder
            input=event.input,
            output=event.output,
            # error=event.error,
        )
        await context.yield_async(tool_end_event.metadata(trajectory))

        if isinstance(event.output, FileCreatorToolOutput):
            result = event.output.result
            for file_info in result.files:
                artifact = Artifact(
                    artifact_id=str(uuid.uuid4()),
                    name=file_info.display_filename,
                    parts=[
                        Part(
                            root=FilePart(
                                file=FileWithUri(
                                    name=file_info.display_filename,
                                    mime_type=file_info.content_type,
                                    uri=str(file_info.url),
                                )
                            )
                        )
                    ],
                )

                await context.yield_async(artifact)

    response = (
        await agent.run()
        .on(
            lambda event: event.name == "start" and isinstance(event.creator, Tool),
            handle_tool_start,
            EmitterOptions(match_nested=True),
        )
        .on(
            lambda event: event.name == "success" and isinstance(event.creator, Tool),
            handle_tool_success,
            EmitterOptions(match_nested=True),
        )
    )

    # async for event, meta in agent.run():
    #     match event:
    #         # case RequirementAgentStartEvent():
    #             # Agent starts processing - no specific tool info yet
    #             # last_step = event.state.steps[-1] if event.state.steps else None
    #             # if last_step and last_step.tool is not None:
    #             #     # Create start event for this tool
    #             #     tool_start_event = ToolCallTrajectoryEvent(
    #             #         kind=last_step.tool.name,
    #             #         phase="start",
    #             #         input=last_step.input,
    #             #         output=None,
    #             #         error=None,
    #             #     )
    #             #     tool_start_events[last_step.id] = tool_start_event
    #             #     yield tool_start_event.metadata(trajectory)

    #         case RequirementAgentSuccessEvent():
    #             last_step = event.state.steps[-1] if event.state.steps else None
    #             if last_step and last_step.tool is not None:
    #                 # Create end event that references the start event
    #                 yield ToolCallTrajectoryEvent(
    #                     kind=last_step.tool.name,
    #                     phase="end",
    #                     parent_event_id=tool_start_events.get(last_step.id),
    #                     input=last_step.input,
    #                     output=last_step.output,
    #                     error=last_step.error,
    #                 ).metadata(trajectory)

    #                 if isinstance(last_step.output, FileCreatorToolOutput):
    #                     result = last_step.output.result
    #                     for file_info in result.files:
    #                         yield Artifact(
    #                             artifact_id=str(uuid.uuid4()),
    #                             name=file_info.display_filename,
    #                             parts=[
    #                                 Part(
    #                                     root=FilePart(
    #                                         file=FileWithUri(
    #                                             name=file_info.display_filename,
    #                                             mime_type=file_info.content_type,
    #                                             uri=str(file_info.url),
    #                                         )
    #                                     )
    #                                 )
    #                             ],
    #                         )

    #             if event.state.answer is not None:
    #                 # Taking a final answer from the state directly instead of RequirementAgentRunOutput to be able to use the final answer provided by the clarification tool
    #                 final_answer = event.state.answer

    #         case _:
    #             # Handle other event types or ignore
    #             continue

    final_answer = response.answer

    if final_answer:
        framework_messages[context.context_id].append(final_answer)

        citations, clean_text = extract_citations(final_answer.text)

        message = AgentMessage(
            text=clean_text,
            metadata=(
                citation.citation_metadata(citations=citations) if citations else None
            ),
        )
        messages[context.context_id].append(message)
        yield message


def serve():
    server.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", 8000)),
        configure_telemetry=True,
    )


if __name__ == "__main__":
    serve()
