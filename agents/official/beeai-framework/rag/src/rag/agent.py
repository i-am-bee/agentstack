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
from beeai_framework.agents.experimental.events import RequirementAgentSuccessEvent
from beeai_framework.backend import ChatModelParameters
from beeai_framework.memory import UnconstrainedMemory
from beeai_framework.middleware.trajectory import GlobalTrajectoryMiddleware
from beeai_framework.tools import Tool
from beeai_sdk.a2a.extensions import (
    AgentDetail,
    AgentDetailTool,
    CitationExtensionServer,
    CitationExtensionSpec,
    TrajectoryExtensionServer,
    TrajectoryExtensionSpec,
)
from beeai_framework.agents.experimental.utils._tool import FinalAnswerTool
from beeai_sdk.a2a.types import AgentMessage
from beeai_sdk.server import Server
from beeai_sdk.server.context import Context
from openai.types import vector_store
from openinference.instrumentation.beeai import BeeAIInstrumentor
from rag.helpers.citations import extract_citations
from rag.helpers.platform import ApiClient
from rag.helpers.trajectory import TrajectoryContent
from rag.helpers.vectore_store import create_vector_store, embed_all_files
from rag.tools.files.file_creator import FileCreatorTool, FileCreatorToolOutput
from rag.tools.files.file_reader import create_file_reader_tool_class
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
vector_store_id: str | None = None # TODO: Implement vector store ID management

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

    # Configure tools
    file_reader_tool_class = create_file_reader_tool_class(
        extracted_files
    )  # Dynamically created tool input schema based on real provided files ensures that small LLMs can't hallucinate the input

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
        # Common tools
        file_reader_tool_class(),
        FileCreatorTool(),
        CurrentTimeTool(),
    ]

    if extracted_files:
        async with ApiClient() as client:
            global vector_store_id
            if vector_store_id is None:
                vector_store_id = await create_vector_store(client)
            yield "Processing files...\n\n"
            tools.append(VectorSearchTool(vector_store_id=vector_store_id))
            await embed_all_files(client, extracted_files, vector_store_id)

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

    async for event, meta in agent.run():
        if not isinstance(event, RequirementAgentSuccessEvent):
            continue

        last_step = event.state.steps[-1] if event.state.steps else None
        if last_step and last_step.tool is not None:
            trajectory_content = TrajectoryContent(
                input=last_step.input,
                output=last_step.output,
                error=last_step.error,
            )
            yield trajectory.trajectory_metadata(
                title=last_step.tool.name,
                content=trajectory_content.model_dump_json(),
            )

            if isinstance(last_step.output, FileCreatorToolOutput):
                result = last_step.output.result
                for file_info in result.files:
                    yield Artifact(
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

        if event.state.answer is not None:
            # Taking a final answer from the state directly instead of RequirementAgentRunOutput to be able to use the final answer provided by the clarification tool
            final_answer = event.state.answer

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
