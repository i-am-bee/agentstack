# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import functools
from collections import defaultdict
import logging
from typing import Annotated
import os

from a2a.types import AgentSkill, Message
from beeai_framework.adapters.openai import OpenAIChatModel
from beeai_framework.agents.experimental import RequirementAgent

from beeai_framework.backend import ChatModelParameters
from beeai_framework.emitter import EmitterOptions
from beeai_framework.memory import UnconstrainedMemory
from beeai_framework.middleware.trajectory import GlobalTrajectoryMiddleware
from beeai_framework.tools import Tool
from openai import AsyncOpenAI

from beeai_sdk.a2a.extensions import (
    AgentDetail,
    CitationExtensionServer,
    CitationExtensionSpec,
    TrajectoryExtensionServer,
    TrajectoryExtensionSpec,
    LLMServiceExtensionServer,
    LLMServiceExtensionSpec,
    EmbeddingServiceExtensionServer,
    EmbeddingServiceExtensionSpec,
)
from beeai_sdk.a2a.extensions.services.platform import (
    PlatformApiExtensionServer,
    PlatformApiExtensionSpec,
)
from beeai_framework.agents.experimental.utils._tool import FinalAnswerTool
from beeai_sdk.a2a.types import AgentMessage, AgentArtifact
from beeai_sdk.server import Server
from beeai_sdk.server.context import RunContext
from openinference.instrumentation.beeai import BeeAIInstrumentor
from rag.helpers.citations import extract_citations
from rag.helpers.trajectory import ToolCallTrajectoryEvent
from rag.helpers.event_binder import EventBinder
from rag.helpers.vectore_store import (
    EmbeddingFunction,
    embed_all_files,
    CreateVectorStoreEvent,
    create_vector_store,
)
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
logging.getLogger("opentelemetry.exporter.otlp.proto.http._log_exporter").setLevel(logging.CRITICAL)
logging.getLogger("opentelemetry.exporter.otlp.proto.http.metric_exporter").setLevel(logging.CRITICAL)

logger = logging.getLogger(__name__)

messages: defaultdict[str, list[Message]] = defaultdict(list)
framework_messages: defaultdict[str, list[FrameworkMessage]] = defaultdict(list)
vector_stores: defaultdict[str, None] = defaultdict(lambda: None)  # TODO: Implement vector store ID management

server = Server()


@server.agent(
    name="RAG",
    documentation_url=(
        f"https://github.com/i-am-bee/beeai-platform/blob/{os.getenv('RELEASE_VERSION', 'main')}"
        "/agents/official/beeai-framework/rag"
    ),
    version="1.0.0",
    default_input_modes=[
        "text/plain",
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # DOCX
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # XLSX
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # PPTX
        "text/markdown",  # Markdown
        "text/asciidoc",  # AsciiDoc
        "text/html",  # HTML
        "application/xhtml+xml",  # XHTML
        "text/csv",  # CSV
        "image/png",  # PNG
        "image/jpeg",  # JPEG
        "image/tiff",  # TIFF
        "image/bmp",  # BMP
        "image/webp",  # WEBP
    ],
    default_output_modes=["text/plain"],
    detail=AgentDetail(
        interaction_mode="multi-turn",
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
    context: RunContext,
    trajectory: Annotated[TrajectoryExtensionServer, TrajectoryExtensionSpec()],
    citation: Annotated[CitationExtensionServer, CitationExtensionSpec()],
    embedding_ext: Annotated[EmbeddingServiceExtensionServer, EmbeddingServiceExtensionSpec.single_demand()],
    llm_ext: Annotated[LLMServiceExtensionServer, LLMServiceExtensionSpec.single_demand()],
    _: Annotated[PlatformApiExtensionServer, PlatformApiExtensionSpec()],
):
    llm, embedding = _get_clients(llm_ext, embedding_ext)

    extracted_files = await extract_files(history=messages[context.context_id], incoming_message=message)

    input = to_framework_message(message)

    # Configure tools
    file_reader_tool_class = create_file_reader_tool_class(
        extracted_files
    )  # Dynamically created tool input schema based on real provided files ensures that small LLMs can't hallucinate the input

    FinalAnswerTool.description = """Assemble and send the final answer to the user. When using information from documents found through search tools, you MUST cite them using markdown citation format: [filename](URL).

# CRITICAL Citation Requirements:
- ALWAYS use markdown format [filename](URL) for document references
- When vector_search or file_reader tools provide URLs, use them in citations
- Use the actual filename (e.g., "Doc1_Mastabas_Administration.pdf") not document IDs
- Place citations inline where the information is referenced
- Do NOT create separate "Citations:" sections - embed citations directly in text

# Examples:
- According to [quarterly-report.pdf](https://platform.com/files/123/content), revenue increased by 15%.
- The analysis in [customer-data.xlsx](https://platform.com/files/456/content) shows improved satisfaction scores.
- Based on findings in [research-paper.pdf](https://platform.com/files/789/content), the hypothesis is supported.

# WRONG Format (avoid this):
"Based on the document..." followed by separate "Citations: - Doc1_file.pdf"

# CORRECT Format (use this):
"Based on [Doc1_file.pdf](https://platform.com/files/123/content), the findings show..."
"""  # type: ignore

    tools = [
        # Auxiliary tools
        ActTool(),  # Enforces correct thinking sequence by requiring tool selection before execution
        ClarificationTool(),  # Allows agent to ask clarifying questions when user requirements are unclear
        CurrentTimeTool(),
        file_reader_tool_class(),
        FileCreatorTool(),
    ]

    if extracted_files:
        if (vector_store_id := vector_stores[context.context_id]) is None:
            start_event = CreateVectorStoreEvent(phase="start")
            yield start_event.metadata(trajectory)

            vector_store_id = (await create_vector_store(embedding)).id
            yield CreateVectorStoreEvent(
                vector_store_id=vector_store_id,
                parent_id=start_event.id,
                phase="end",
            ).metadata(trajectory)

        tools.append(VectorSearchTool(vector_store_id=vector_store_id, embedding_function=embedding))
        async for item in embed_all_files(
            embedding_function=embedding,
            all_files=extracted_files,
            vector_store_id=vector_store_id,
            trajectory=trajectory,
        ):
            yield item

    requirements = [
        ActAlwaysFirstRequirement(),  #  Enforces the ActTool to be used before any other tool execution.
    ]

    # Build dynamic instructions based on available files
    base_instructions = (
        "You are a helpful assistant that answers questions about uploaded documents. "
        "Choose the appropriate tool based on the task:\n"
        "- Use 'file_reader' ONLY for: summarizing entire files or documents when the user explicitly "
        "requests a complete summary or overview of the whole file\n"
        "- Use 'vector_search' for: finding specific information within documents, answering questions "
        "about particular topics or concepts, research queries, and any targeted information retrieval\n"
        "Always search or read relevant information first, then provide a comprehensive response."
    )

    if extracted_files:
        files_info = "\n\nAvailable files:\n"
        for file in extracted_files:
            files_info += f"- ID: {file.id}, Filename: {file.filename}, Url: {file.url}\n"
        instructions = base_instructions + files_info
    else:
        instructions = base_instructions

    # Create agent
    agent = RequirementAgent(
        llm=llm,
        tools=tools,
        memory=UnconstrainedMemory(),
        instructions=instructions,
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
        logger.info("Handle tool start")
        # Store the start event ID using EventBinder
        event_binder.set_start_event_id(meta)

        event_id = event_binder.get_event_id(meta)
        logger.info(f"event_id: {event_id}")
        logger.info(f"meta.trace.id: {meta.trace.id}")
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
        logger.info("Handle tool success")
        # Get the corresponding start event ID using EventBinder
        start_event_id = event_binder.get_start_event_id(meta)

        event_id = event_binder.get_event_id(meta)
        logger.info(f"event_id: {event_id}")
        logger.info(f"start_event_id: {start_event_id}")
        logger.info(f"meta.trace.id: {meta.trace.id}")
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
            for file in result.files:
                artifact = AgentArtifact(name=file.filename, parts=[file.to_file_part()])
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

    final_answer = response.answer

    if final_answer:
        framework_messages[context.context_id].append(final_answer)

        citations, clean_text = extract_citations(final_answer.text)

        message = AgentMessage(
            text=clean_text,
            metadata=(citation.citation_metadata(citations=citations) if citations else None),
        )
        messages[context.context_id].append(message)
        yield message


def _get_clients(
    llm_ext: LLMServiceExtensionServer, embedding_ext: EmbeddingServiceExtensionServer
) -> tuple[OpenAIChatModel, EmbeddingFunction]:
    llm_conf, embedding_conf = None, None
    if llm_ext:
        [llm_conf] = llm_ext.data.llm_fulfillments.values()
    if embedding_ext:
        [embedding_conf] = embedding_ext.data.embedding_fulfillments.values()

    llm = OpenAIChatModel(
        model_id=llm_conf.api_model if llm_conf else "llama3.1",
        api_key=llm_conf.api_key if llm_conf else "dummy",
        base_url=llm_conf.api_base if llm_conf else "http://localhost:11434/v1",
        parameters=ChatModelParameters(temperature=0.0),
        tool_choice_support=set(),
    )

    embedding_client = AsyncOpenAI(
        api_key=embedding_conf.api_key if embedding_conf else "dummy",
        base_url=embedding_conf.api_base if embedding_conf else "http://localhost:11434/v1",
    )
    embedding = functools.partial(
        embedding_client.embeddings.create,
        encoding_format="float",
        model=embedding_conf.api_model if embedding_conf else "dummy",
    )
    return llm, embedding


def serve():
    server.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", 8000)),
        configure_telemetry=True,
    )


if __name__ == "__main__":
    serve()
