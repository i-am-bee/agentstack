# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import logging
import os
from typing import Annotated
import uuid
from collections import defaultdict
from textwrap import dedent

from a2a.types import (
    AgentSkill,
    Artifact,
    FilePart,
    FileWithUri,
    Message,
    Part,
)
from beeai_framework.adapters.openai import OpenAIChatModel
from beeai_framework.agents.experimental import (
    RequirementAgent,
)
from beeai_framework.agents.experimental.events import (
    RequirementAgentSuccessEvent,
)
from beeai_framework.agents.experimental.utils._tool import FinalAnswerTool
from beeai_framework.backend.types import ChatModelParameters
from beeai_framework.emitter import EventMeta
from beeai_framework.memory import UnconstrainedMemory
from beeai_framework.middleware.trajectory import GlobalTrajectoryMiddleware
from beeai_framework.tools import Tool
from beeai_framework.tools.search.duckduckgo import DuckDuckGoSearchTool
from beeai_framework.tools.search.wikipedia import WikipediaTool

from beeai_framework.tools.weather import OpenMeteoTool
from beeai_sdk.a2a.extensions import (
    AgentDetail,
    AgentDetailTool,
    CitationExtensionServer,
    CitationExtensionSpec,
    TrajectoryExtensionServer,
    TrajectoryExtensionSpec,
)
from beeai_sdk.a2a.types import AgentMessage
from beeai_sdk.server import Server
from beeai_sdk.server.context import Context
from chat.tools.general.current_time import CurrentTimeTool
from chat.helpers.citations import extract_citations
from chat.helpers.trajectory import TrajectoryContent
from openinference.instrumentation.beeai import BeeAIInstrumentor

from chat.tools.files.file_creator import FileCreatorTool, FileCreatorToolOutput
from chat.tools.files.file_reader import create_file_reader_tool_class
from chat.tools.files.utils import FrameworkMessage, extract_files, to_framework_message
from chat.tools.general.act import (
    ActAlwaysFirstRequirement,
    ActTool,
    act_tool_middleware,
)
from chat.tools.general.clarification import (
    ClarificationTool,
    clarification_tool_middleware,
)

# Temporary instrument fix
EventMeta.to_json_safe = lambda self: self.model_dump(
    exclude_none=True, exclude={"context"}
)

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

server = Server()


@server.agent(
    name="Chat",
    documentation_url=(
        f"https://github.com/i-am-bee/beeai-platform/blob/{os.getenv('RELEASE_VERSION', 'main')}"
        "/agents/official/beeai-framework/chat"
    ),
    version="1.0.0",
    default_input_modes=["text", "text/plain"],
    default_output_modes=["text", "text/plain"],
    detail=AgentDetail(
        ui_type="chat",
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
    ),
    skills=[
        AgentSkill(
            id="chat",
            name="Chat",
            description=dedent(
                """\
                The agent is an AI-powered conversational system designed to process user messages, maintain context,
                and generate intelligent responses. Built on the **BeeAI framework**, it leverages memory and external
                tools to enhance interactions. It supports real-time web search, Wikipedia lookups, and weather updates,
                making it a versatile assistant for various applications.
            
                ## How It Works
                The agent processes incoming messages and maintains a conversation history using an **unconstrained
                memory module**. It utilizes a language model (`CHAT_MODEL`) to generate responses and can optionally
                integrate external tools for additional functionality.
            
                It supports:
                - **Web Search (DuckDuckGo)** – Retrieves real-time search results.
                - **Wikipedia Search** – Fetches summaries from Wikipedia.
                - **Weather Information (OpenMeteo)** – Provides real-time weather updates.
            
                The agent also includes an **event-based streaming mechanism**, allowing it to send partial responses
                to clients as they are generated.
            
                ## Key Features
                - **Conversational AI** – Handles multi-turn conversations with memory.
                - **Tool Integration** – Supports real-time search, Wikipedia lookups, and weather updates.
                - **Event-Based Streaming** – Can send partial updates to clients as responses are generated.
                - **Customizable Configuration** – Users can enable or disable specific tools for enhanced responses.
                """
            ),
            tags=["chat"],
            examples=[
                "Please find a room in LA, CA, April 15, 2025, checkout date is april 18, 2 adults"
            ],
        )
    ],
)
async def chat(
    message: Message,
    context: Context,
    trajectory: Annotated[TrajectoryExtensionServer, TrajectoryExtensionSpec()],
    citation: Annotated[CitationExtensionServer, CitationExtensionSpec()],
):
    """
    The agent is an AI-powered conversational system with memory, supporting real-time search, Wikipedia lookups,
    and weather updates through integrated tools.
    """
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
