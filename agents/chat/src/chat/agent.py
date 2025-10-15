# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import logging
import os
from typing import Annotated
from textwrap import dedent

from a2a.types import (
    AgentSkill,
    Message,
)
from beeai_framework.adapters.beeai_platform.backend.chat import BeeAIPlatformChatModel
from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.agents.requirement.events import (
    RequirementAgentSuccessEvent,
)
from beeai_framework.agents.requirement.utils._tool import FinalAnswerTool
from beeai_framework.emitter import EventMeta
from beeai_framework.memory import UnconstrainedMemory
from beeai_framework.middleware.trajectory import GlobalTrajectoryMiddleware
from beeai_framework.tools import Tool
from beeai_framework.tools.search.duckduckgo import DuckDuckGoSearchTool
from beeai_framework.tools.search.wikipedia import WikipediaTool
from beeai_framework.tools.weather import OpenMeteoTool
from beeai_framework.backend import ChatModelParameters
from beeai_sdk.a2a.extensions import (
    AgentDetail,
    AgentDetailContributor,
    AgentDetailTool,
    CitationExtensionServer,
    CitationExtensionSpec,
    TrajectoryExtensionServer,
    TrajectoryExtensionSpec,
    LLMServiceExtensionServer,
    LLMServiceExtensionSpec,
)
from beeai_sdk.a2a.extensions.services.platform import (
    PlatformApiExtensionServer,
    PlatformApiExtensionSpec,
)
from beeai_sdk.a2a.types import AgentMessage, AgentArtifact
from beeai_sdk.server import Server
from beeai_sdk.server.context import RunContext
from openinference.instrumentation.beeai import BeeAIInstrumentor

from chat.helpers.citations import extract_citations
from chat.helpers.trajectory import TrajectoryContent
from chat.tools.files.file_creator import FileCreatorTool, FileCreatorToolOutput
from chat.tools.files.file_reader import create_file_reader_tool_class
from chat.tools.files.utils import extract_files, to_framework_message
from chat.tools.general.act import (
    ActAlwaysFirstRequirement,
    ActTool,
    act_tool_middleware,
)
from chat.tools.general.clarification import (
    ClarificationTool,
    clarification_tool_middleware,
)
from chat.tools.general.current_time import CurrentTimeTool

from beeai_sdk.server.store.platform_context_store import PlatformContextStore

# Temporary instrument fix
EventMeta.model_fields["context"].exclude = True

BeeAIInstrumentor().instrument()
## TODO: https://github.com/phoenixframework/phoenix/issues/6224
logging.getLogger("opentelemetry.exporter.otlp.proto.http._log_exporter").setLevel(logging.CRITICAL)
logging.getLogger("opentelemetry.exporter.otlp.proto.http.metric_exporter").setLevel(logging.CRITICAL)

logger = logging.getLogger(__name__)

server = Server()


@server.agent(
    name="Chat",
    documentation_url=(
        f"https://github.com/i-am-bee/beeai-platform/blob/{os.getenv('RELEASE_VERSION', 'main')}/agents/chat"
    ),
    version="1.0.0",
    default_input_modes=["text", "text/plain"],
    default_output_modes=["text", "text/plain"],
    detail=AgentDetail(
        interaction_mode="multi-turn",
        user_greeting="How can I help you?",
        tools=[
            AgentDetailTool(
                name="Act Tool",
                description="Auxiliary tool that ensures thoughtful tool selection by requiring explicit reasoning and tool choice before executing any other tool.",
            ),
            AgentDetailTool(
                name="Clarification Tool",
                description="Enables the agent to ask clarifying questions when user requirements are unclear, preventing assumptions and ensuring accurate task completion.",
            ),
            AgentDetailTool(
                name="Wikipedia Search",
                description="Fetches summaries and information from Wikipedia articles.",
            ),
            AgentDetailTool(
                name="Weather Information (OpenMeteo)",
                description="Provides real-time weather updates and forecasts.",
            ),
            AgentDetailTool(
                name="Web Search (DuckDuckGo)",
                description="Retrieves real-time search results from the web.",
            ),
            AgentDetailTool(
                name="File Reader",
                description="Reads and returns content from uploaded or generated files.",
            ),
            AgentDetailTool(
                name="File Creator",
                description="Creates new files with specified content and metadata, uploading them to the platform for download or further processing.",
            ),
            AgentDetailTool(
                name="Current Time",
                description="Provides current date and time information.",
            ),
        ],
        framework="BeeAI",
        programming_language="Python",
        author=AgentDetailContributor(name="BeeAI contributors"),
        contributors=[],
        license="Apache 2.0",
    ),
    skills=[
        AgentSkill(
            id="chat",
            name="Chat",
            description=dedent(
                """\
                The agent is an AI-powered conversational system designed to process user messages, maintain context,
                and generate intelligent responses. Built on the **BeeAI framework**, it leverages memory and external
                tools to enhance interactions. It supports real-time web search, Wikipedia lookups, file manipulations,
                and weather updates, making it a versatile assistant for various applications.

                ## How It Works
                The agent processes incoming messages and maintains a conversation history using an **unconstrained
                memory module**. It utilizes a language model (`CHAT_MODEL`) to generate responses and can optionally
                integrate external tools for additional functionality. The agent is basically a ReAct agent built on 
                top of a Requirement agent. It uses auxiliary tools like Act Tool and Clarification Tool to enhance its
                capabilities for smaller models.

                It supports:
                - **Web Search (DuckDuckGo)** – Retrieves real-time search results.
                - **Wikipedia Search** – Fetches summaries from Wikipedia.
                - **Weather Information (OpenMeteo)** – Provides real-time weather updates.
                - **File Reader** – Reads and returns content from uploaded files.
                - **File Creator** – Creates new files with specified content and metadata.
                - **Current Time** – Provides current date and time information.

                The agent also includes an **event-based streaming mechanism**, allowing it to send partial responses
                to clients as they are generated.
            
                ## Key Features
                - **Conversational AI** – Handles multi-turn conversations with memory.
                - **Tool Integration** – Supports real-time search, Wikipedia lookups, files manipulations, and weather updates.
                - **Event-Based Streaming** – Can send partial updates to clients as responses are generated.
                """
            ),
            tags=["chat"],
            examples=["Please find a room in LA, CA, April 15, 2025, checkout date is april 18, 2 adults"],
        )
    ],
)
async def chat(
    input: Message,
    context: RunContext,
    trajectory: Annotated[TrajectoryExtensionServer, TrajectoryExtensionSpec()],
    citation: Annotated[CitationExtensionServer, CitationExtensionSpec()],
    llm_ext: Annotated[
        LLMServiceExtensionServer,
        LLMServiceExtensionSpec.single_demand(suggested=("openai:gpt-4o", "ollama:granite3.3:8b")),
    ],
    _: Annotated[PlatformApiExtensionServer, PlatformApiExtensionSpec()],
):
    """Agent with memory and access to web search, Wikipedia, and weather."""
    await context.store(input)
    history = [message async for message in context.load_history() if isinstance(message, Message) and message.parts]
    extracted_files = await extract_files(history=history)

    # Configure tools
    file_reader_tool_class = create_file_reader_tool_class(
        extracted_files
    )  # Dynamically created tool input schema based on real provided files ensures that small LLMs can't hallucinate the input

    FinalAnswerTool.description = dedent("""\
        Assemble and send the final answer to the user. When using information gathered from other tools that provided URL addresses, you MUST properly cite them using markdown citation format: [description](URL).

        # Citation Requirements:
        - Use descriptive text that summarizes the source content
        - Include the exact URL provided by the tool
        - Place citations inline where the information is referenced

        # Examples:
        - According to [OpenAI's latest announcement](https://example.com/gpt5), GPT-5 will be released next year.
        - Recent studies show [AI adoption has increased by 67%](https://example.com/ai-study) in enterprise environments.
        - Weather data indicates [temperatures will reach 25°C tomorrow](https://weather.example.com/forecast).
        """)  # type: ignore

    tools = [
        # Auxiliary tools
        ActTool(),  # Enforces correct thinking sequence by requiring tool selection before execution
        ClarificationTool(),  # Allows agent to ask clarifying questions when user requirements are unclear
        # Common tools
        WikipediaTool(),
        OpenMeteoTool(),
        DuckDuckGoSearchTool(),
        file_reader_tool_class(),
        FileCreatorTool(),
        CurrentTimeTool(),
    ]

    requirements = [
        ActAlwaysFirstRequirement(),  #  Enforces the ActTool to be used before any other tool execution.
    ]

    use_streaming = True
    llm = BeeAIPlatformChatModel(parameters=ChatModelParameters(stream=use_streaming))
    llm.set_context(llm_ext)

    # Build dynamic instructions based on available files
    base_instructions = dedent(
        """\
        You are a helpful AI assistant built on the BeeAI framework. You have access to various tools and capabilities to assist users effectively.

        ## Core Behavior Guidelines:
        - Always be helpful, accurate, and concise in your responses
        - Use the Act Tool before executing any other tools to ensure thoughtful reasoning
        - When user requirements are unclear, use the Clarification Tool to ask specific questions
        - Maintain conversation context and refer to previous messages when relevant

        ## Tool Usage:
        - **Act Tool**: Required before using any other tool - explain your reasoning and tool choice
        - **Clarification Tool**: Ask clarifying questions when user intent is ambiguous
        - **Web Search (DuckDuckGo)**: For real-time information, current events, and general web searches
        - **Wikipedia Search**: For encyclopedic information and factual summaries
        - **Weather Tool (OpenMeteo)**: For current weather conditions and forecasts
        - **File Reader**: To read content from uploaded files (when available)
        - **File Creator**: To create new files with specific content and metadata
        - **Current Time**: For date and time information

        ## Citation Requirements:
        When using information from tools that provide URLs, you MUST cite sources using markdown format:
        - Format: [descriptive text](URL)
        - Place citations inline where information is referenced
        - Use descriptive text that summarizes the source content

        ## File Handling:
        - When files are available, reference them by ID and filename
        - Read file contents when users ask about uploaded documents
        - Create files when users need downloadable content
        {file_context}

        ## Response Quality:
        - Provide comprehensive, well-structured answers
        - Break down complex topics into digestible sections
        - Use appropriate formatting (headers, lists, code blocks) when helpful
        - Always complete tasks fully before providing final answers
        """
    )

    if extracted_files:
        files_context = "\n\n## Currently Available Files:"
        files_context += "\nThe user has uploaded the following files that you can access using the File Reader tool:"
        for file in extracted_files:
            files_context += f"\n- **{file.file.filename}** (ID: {file.file.id}) - Available at: {file.file.url}"
        files_context += (
            "\n\nWhen referencing these files, use their ID with the File Reader tool to access their content."
        )
        instructions = base_instructions.format(file_context=files_context)
    else:
        instructions = base_instructions.format(file_context="")

    # Create agent
    agent = RequirementAgent(
        llm=llm,
        tools=tools,
        memory=UnconstrainedMemory(),
        requirements=requirements,
        instructions=instructions,
        middlewares=[
            GlobalTrajectoryMiddleware(included=[Tool]),  # ChatModel,
            act_tool_middleware,
            clarification_tool_middleware,
        ],
    )

    final_answer = None
    new_messages = [to_framework_message(item, extracted_files) for item in history]

    async for event, meta in agent.run(new_messages):
        if not isinstance(event, RequirementAgentSuccessEvent):
            continue

        last_step = event.state.steps[-1] if event.state.steps else None
        if last_step and last_step.tool is not None and last_step.tool.name != FinalAnswerTool.name:
            trajectory_content = TrajectoryContent(
                input=last_step.input,
                output=last_step.output,
                error=last_step.error,
            )
            metadata = trajectory.trajectory_metadata(
                title=last_step.tool.name,
                content=trajectory_content.model_dump_json(),
            )
            yield metadata
            await context.store(AgentMessage(metadata=metadata))

            if isinstance(last_step.output, FileCreatorToolOutput):
                result = last_step.output.result
                for file_info in result.files:
                    part = file_info.file.to_file_part()
                    part.file.name = file_info.display_filename
                    artifact = AgentArtifact(name=file_info.display_filename, parts=[part])
                    yield artifact
                    await context.store(artifact)

        if event.state.answer is not None:
            # Taking a final answer from the state directly instead of RequirementAgentRunOutput to be able to use the final answer provided by the clarification tool
            final_answer = event.state.answer

    if final_answer:
        citations, clean_text = extract_citations(final_answer.text)

        message = AgentMessage(
            text=clean_text,
            metadata=(citation.citation_metadata(citations=citations) if citations else None),
        )
        if not use_streaming:
            yield message
        await context.store(message)


def serve():
    try:
        server.run(
            host=os.getenv("HOST", "127.0.0.1"),
            port=int(os.getenv("PORT", 8000)),
            configure_telemetry=True,
            context_store=PlatformContextStore(),
        )
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    serve()
