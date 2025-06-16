import os
import logging
from collections.abc import AsyncGenerator
from textwrap import dedent

import beeai_framework
from acp_sdk import Message, Metadata, Link, LinkType
from acp_sdk.models import MessagePart
from acp_sdk.server import Context, Server
from beeai_framework.agents.react import ReActAgent, ReActAgentUpdateEvent
from beeai_framework.backend import AssistantMessage, Role, UserMessage
from beeai_framework.backend.chat import ChatModel, ChatModelParameters
from beeai_framework.memory import UnconstrainedMemory
from beeai_framework.tools.search.duckduckgo import DuckDuckGoSearchTool
from beeai_framework.tools.search.wikipedia import WikipediaTool
from beeai_framework.tools.tool import AnyTool
from beeai_framework.tools.weather.openmeteo import OpenMeteoTool
from pydantic import AnyUrl
from openinference.instrumentation.beeai import BeeAIInstrumentor

BeeAIInstrumentor().instrument()
## TODO: https://github.com/phoenixframework/phoenix/issues/6224
logging.getLogger("opentelemetry.exporter.otlp.proto.http._log_exporter").setLevel(logging.CRITICAL)
logging.getLogger("opentelemetry.exporter.otlp.proto.http.metric_exporter").setLevel(logging.CRITICAL)

server = Server()


def to_framework_message(role: Role, content: str) -> beeai_framework.backend.Message:
    match role:
        case Role.USER:
            return UserMessage(content)
        case Role.ASSISTANT:
            return AssistantMessage(content)
        case _:
            raise ValueError(f"Unsupported role {role}")


@server.agent(
    metadata=Metadata(
        programming_language="Python",
        links=[
            Link(
                type=LinkType.SOURCE_CODE,
                url=AnyUrl(
                    f"https://github.com/i-am-bee/beeai-platform/blob/{os.getenv('RELEASE_VERSION', 'main')}"
                    "/agents/official/beeai-framework/chat"
                ),
            )
        ],
        license="Apache 2.0",
        framework="BeeAI",
        documentation=dedent(
            """\
            The agent is an AI-powered conversational system designed to process user messages, maintain context,
            and generate intelligent responses. Built on the **BeeAI framework**, it leverages memory and external 
            tools to enhance interactions. It supports real-time web search, Wikipedia lookups, and weather updates,
            making it a versatile assistant for various applications.

            ## How It Works
            The agent processes incoming messages and maintains a conversation history using an **unconstrained 
            memory module**. It utilizes a language model (\`CHAT_MODEL\`) to generate responses and can optionally 
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
        use_cases=[
            "**Chatbots** – Can be used in AI-powered chat applications with memory.",
            "**Research Assistance** – Retrieves relevant information from web search and Wikipedia.",
            "**Weather Inquiries** – Provides real-time weather updates based on location.",
            "**Agents with Long-Term Memory** – Maintains context across conversations for improved interactions.",
        ],
        ui={"type": "chat", "user_greeting": "How can I help you?"},
        annotations={"display_name": "Chat"},
        examples={
            "cli": [
                {
                    "command": 'beeai run chat "What is the weather like in Paris?',
                    "name": "With tools",
                    "description": "Run agent with tools.",
                    "output": "The current temperature in Paris is 12°C with partly cloudy skies.",
                    "processing_steps": [
                        "The agent receives the user message and detects the weather query",
                        "It invokes the OpenMeteoTool to fetch real-time weather data",
                        "The response is generated and sent back to the user",
                    ],
                },
            ]
        },
        env=[
            {"name": "LLM_MODEL", "description": "Model to use from the specified OpenAI-compatible API."},
            {"name": "LLM_API_BASE", "description": "Base URL for OpenAI-compatible API endpoint"},
            {"name": "LLM_API_KEY", "description": "API key for OpenAI-compatible API endpoint"},
        ],
    )
)
async def chat(input: list[Message], context: Context) -> AsyncGenerator:
    """
    The agent is an AI-powered conversational system with memory, supporting real-time search, Wikipedia lookups,
    and weather updates through integrated tools.
    """

    # ensure the model is pulled before running
    os.environ["OPENAI_API_BASE"] = os.getenv("LLM_API_BASE", "http://localhost:11434/v1")
    os.environ["OPENAI_API_KEY"] = os.getenv("LLM_API_KEY", "dummy")
    llm = ChatModel.from_name(f"openai:{os.getenv('LLM_MODEL', 'llama3.1')}", ChatModelParameters(temperature=0))

    # Configure tools
    tools: list[AnyTool] = [WikipediaTool(), OpenMeteoTool(), DuckDuckGoSearchTool()]

    # Create agent with memory and tools
    agent = ReActAgent(llm=llm, tools=tools, memory=UnconstrainedMemory())

    framework_messages = [to_framework_message(Role(message.parts[0].role), str(message)) for message in input]
    await agent.memory.add_many(framework_messages)

    async for data, event in agent.run():
        match (data, event.name):
            case (ReActAgentUpdateEvent(), "partial_update"):
                update = data.update.value
                if not isinstance(update, str):
                    update = update.get_text_content()
                match data.update.key:
                    case "thought" | "tool_name" | "tool_input" | "tool_output":
                        yield {data.update.key: update}
                    case "final_answer":
                        yield MessagePart(content=update, role="assistant")


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)), configure_telemetry=True)


if __name__ == "__main__":
    run()
