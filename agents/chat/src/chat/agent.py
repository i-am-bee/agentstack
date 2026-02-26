# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import logging
import os
from textwrap import dedent
from typing import Annotated

from a2a.types import (
    AgentSkill,
    Message,
)
from agentstack_sdk.a2a.extensions import (
    AgentDetail,
    AgentDetailContributor,
    AgentDetailTool,
    CitationExtensionServer,
    CitationExtensionSpec,
    ErrorExtensionParams,
    ErrorExtensionServer,
    ErrorExtensionSpec,
    LLMServiceExtensionServer,
    LLMServiceExtensionSpec,
    TrajectoryExtensionServer,
    TrajectoryExtensionSpec,
)
from agentstack_sdk.a2a.extensions.services.platform import (
    PlatformApiExtensionServer,
    PlatformApiExtensionSpec,
)
from agentstack_sdk.a2a.types import AgentArtifact, AgentMessage
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext
from agentstack_sdk.server.middleware.platform_auth_backend import PlatformAuthBackend
from agentstack_sdk.server.store.platform_context_store import PlatformContextStore
from beeai_framework.adapters.agentstack.backend.chat import AgentStackChatModel
from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.agents.requirement.events import (
    RequirementAgentFinalAnswerEvent,
    RequirementAgentSuccessEvent,
)
from beeai_framework.agents.requirement.utils._tool import FinalAnswerTool
from beeai_framework.backend import AssistantMessage, ChatModelParameters
from beeai_framework.errors import FrameworkError
from beeai_framework.middleware.trajectory import GlobalTrajectoryMiddleware
from beeai_framework.tools import AnyTool, Tool
from beeai_framework.tools.search.duckduckgo import DuckDuckGoSearchTool
from beeai_framework.tools.search.wikipedia import WikipediaTool
from beeai_framework.tools.weather import OpenMeteoTool
from openinference.instrumentation.beeai import BeeAIInstrumentor

from chat.helpers.citations import extract_citations
from chat.helpers.trajectory import TrajectoryContent
from chat.tools.files.file_creator import FileCreatorTool, FileCreatorToolOutput
from chat.tools.files.file_reader import FileReaderTool
from chat.tools.files.utils import extract_files, to_framework_message

beeai_instrumentor = BeeAIInstrumentor()
if beeai_instrumentor:
    beeai_instrumentor.instrument()

logger = logging.getLogger(__name__)

server = Server()


@server.agent(
    name="Chat",
    documentation_url=(
        f"https://github.com/i-am-bee/agentstack/blob/{os.getenv('RELEASE_VERSION', 'main')}/agents/chat"
    ),
    version="1.0.0",
    default_input_modes=["text", "text/plain"],
    default_output_modes=["text", "text/plain"],
    detail=AgentDetail(
        interaction_mode="multi-turn",
        user_greeting="How can I help you?",
        tools=[
            AgentDetailTool(
                name="Wikipedia Search",
                description="Fetches summaries and information from Wikipedia articles.",
            ),
            AgentDetailTool(
                name="Weather Information (OpenMeteo)", description="Provides real-time weather updates and forecasts."
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
                memory module**. It utilizes a language model to generate responses and can optionally
                integrate external tools for additional functionality. The agent is basically a ReAct agent built on 
                top of a Requirement agent.

                It supports:
                - **Web Search (DuckDuckGo)** – Retrieves real-time search results.
                - **Wikipedia Search** – Fetches summaries from Wikipedia.
                - **Weather Information (OpenMeteo)** – Provides real-time weather updates.
                - **File Reader** – Reads and returns content from uploaded files.
                - **File Creator** – Creates new files with specified content and metadata.

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
        LLMServiceExtensionSpec.single_demand(),
    ],
    _e: Annotated[ErrorExtensionServer, ErrorExtensionSpec(ErrorExtensionParams(include_stacktrace=True))],
    _p: Annotated[PlatformApiExtensionServer, PlatformApiExtensionSpec()],
):
    """Agent with memory and access to web search, Wikipedia, and weather."""
    await context.store(input)

    # Send initial trajectory
    yield trajectory.trajectory_metadata(title="Starting", content="Received your request")

    history = [message async for message in context.load_history() if isinstance(message, Message) and message.parts]
    extracted_files = await extract_files(history=history)

    llm = AgentStackChatModel(parameters=ChatModelParameters(stream=True))
    llm.set_context(llm_ext)

    # Build dynamic instructions based on available files
    base_instructions = dedent(
        """\
        You are a helpful AI assistant built on the BeeAI framework. You have access to various tools and capabilities to assist users effectively.

        ## Core Behavior Guidelines:
        - Always be helpful, accurate, and concise in your responses
        - Maintain conversation context and refer to previous messages when relevant

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

    # Configure tools
    tools: list[AnyTool] = [
        WikipediaTool(),
        OpenMeteoTool(),
        DuckDuckGoSearchTool(),
        FileCreatorTool(),
    ]

    if extracted_files:
        # Dynamically created tool input schema based on real provided files ensures that small LLMs can't hallucinate the input
        tools.append(FileReaderTool(extracted_files))

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
        instructions=instructions,
        middlewares=[GlobalTrajectoryMiddleware(included=[Tool])],
    )

    final_answer: AssistantMessage | None = None
    new_messages = [to_framework_message(item, extracted_files) for item in history]

    try:
        async for event, meta in agent.run(
            new_messages,
            expected_output=dedent("""\
               Assemble and send the final answer to the user. When using information gathered from other tools that provided URL addresses, you MUST properly cite them using markdown citation format: [description](URL).
    
               # Citation Requirements:
               - Use descriptive text that summarizes the source content
               - Include the exact URL provided by the tool
               - Place citations inline where the information is referenced
    
               # Examples:
               - According to [OpenAI's latest announcement](https://example.com/gpt5), GPT-5 will be released next year.
               - Recent studies show [AI adoption has increased by 67%](https://example.com/ai-study) in enterprise environments.
               - Weather data indicates [temperatures will reach 25°C tomorrow](https://weather.example.com/forecast).
               """),
        ):
            match event:
                case RequirementAgentFinalAnswerEvent(delta=delta):
                    yield delta
                case RequirementAgentSuccessEvent(state=state):
                    final_answer = state.answer

                    last_step = state.steps[-1]
                    if last_step.tool and last_step.tool.name == FinalAnswerTool.name:  # internal tool
                        continue

                    trajectory_content = TrajectoryContent(
                        input=last_step.input, output=last_step.output, error=last_step.error
                    )
                    metadata = trajectory.trajectory_metadata(
                        title=last_step.tool.name if last_step.tool else None, content=trajectory_content.model_dump_json(), group_id=last_step.id
                    )
                    yield metadata
                    await context.store(AgentMessage(metadata=metadata))

                    if isinstance(last_step.output, FileCreatorToolOutput):
                        for file_info in last_step.output.result.files:
                            part = file_info.file.to_file_part()
                            part.file.name = file_info.display_filename
                            artifact = AgentArtifact(name=file_info.display_filename, parts=[part])
                            yield artifact
                            await context.store(artifact)

        if final_answer:
            citations, clean_text = extract_citations(final_answer.text)

            message = AgentMessage(
                text=clean_text,
                metadata=(citation.citation_metadata(citations=citations) if citations else None),
            )
            await context.store(message)
    except FrameworkError as err:
        raise RuntimeError(err.explain())


def serve():
    try:
        server.run(
            host=os.getenv("HOST", "127.0.0.1"),
            port=int(os.getenv("PORT", 8000)),
            configure_telemetry=True,
            context_store=PlatformContextStore(),
            auth_backend=PlatformAuthBackend(),
        )
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    serve()
