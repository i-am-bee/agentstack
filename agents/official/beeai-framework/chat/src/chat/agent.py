# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import logging
import os
import uuid
from collections import defaultdict
from textwrap import dedent

from a2a.types import Message, Role, AgentCapabilities, AgentSkill, AgentExtension, TextPart, Part
from beeai_framework.agents.react import ReActAgent, ReActAgentUpdateEvent
from beeai_framework.backend import AssistantMessage, UserMessage
from beeai_framework.backend.chat import ChatModel, ChatModelParameters
from beeai_framework.memory import UnconstrainedMemory
from beeai_framework.tools.search.duckduckgo import DuckDuckGoSearchTool
from beeai_framework.tools.search.wikipedia import WikipediaTool
from beeai_framework.tools.tool import AnyTool
from beeai_framework.tools.weather.openmeteo import OpenMeteoTool
from openinference.instrumentation.beeai import BeeAIInstrumentor

from beeai_sdk.server.context import Context
from beeai_sdk.server import Server

BeeAIInstrumentor().instrument()
## TODO: https://github.com/phoenixframework/phoenix/issues/6224
logging.getLogger("opentelemetry.exporter.otlp.proto.http._log_exporter").setLevel(logging.CRITICAL)
logging.getLogger("opentelemetry.exporter.otlp.proto.http.metric_exporter").setLevel(logging.CRITICAL)


logger = logging.getLogger(__name__)
SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

messages: defaultdict[str, list[UserMessage | AssistantMessage]] = defaultdict(list)


def to_framework_message(message: Message) -> UserMessage | AssistantMessage:
    message_text = "".join(part.root.text for part in message.parts if part.root.kind == "text")

    if message.role == Role.agent:
        return AssistantMessage(message_text)

    if message.role == Role.user:
        return UserMessage(message_text)

    raise ValueError(f"Invalid message role: {message.role}")


server = Server()


@server.agent(
    documentation_url=(
        f"https://github.com/i-am-bee/beeai-platform/blob/{os.getenv('RELEASE_VERSION', 'main')}"
        "/agents/official/beeai-framework/chat"
    ),
    version="1.0.0",
    default_input_modes=SUPPORTED_CONTENT_TYPES,
    default_output_modes=SUPPORTED_CONTENT_TYPES,
    capabilities=AgentCapabilities(
        streaming=True,
        push_notifications=True,
        extensions=[
            AgentExtension(
                uri="beeai_ui",
                params={
                    "ui_type": "chat",
                    "user_greeting": "How can I help you?",
                    "display_name": "Chat",
                    "tools": [
                        {
                            "name": "Web Search (DuckDuckGo)",
                            "description": "Retrieves real-time search results.",
                        },
                        {
                            "name": "Wikipedia Search",
                            "description": "Fetches summaries from Wikipedia.",
                        },
                        {
                            "name": "Weather Information (OpenMeteo)",
                            "description": "Provides real-time weather updates.",
                        },
                    ],
                },
            )
        ],
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
            examples=["Please find a room in LA, CA, April 15, 2025, checkout date is april 18, 2 adults"],
        )
    ],
)
async def chat(message: Message, context: Context):
    """
    The agent is an AI-powered conversational system with memory, supporting real-time search, Wikipedia lookups,
    and weather updates through integrated tools.
    """
    # ensure the model is pulled before running
    os.environ["OPENAI_API_BASE"] = os.getenv("LLM_API_BASE", "http://localhost:11434/v1")
    os.environ["OPENAI_API_KEY"] = os.getenv("LLM_API_KEY", "dummy")
    llm = ChatModel.from_name(
        f"openai:{os.getenv('LLM_MODEL', 'llama3.1')}",
        ChatModelParameters(temperature=0),
    )

    # Configure tools
    tools: list[AnyTool] = [
        WikipediaTool(),
        OpenMeteoTool(),
        DuckDuckGoSearchTool(),
    ]

    # Create agent with memory and tools
    agent = ReActAgent(llm=llm, tools=tools, memory=UnconstrainedMemory())

    messages[context.context_id].append(to_framework_message(message))

    await agent.memory.add_many(messages[context.context_id])
    final_answer = ""

    async for data, event in agent.run():
        match (data, event.name):
            case (ReActAgentUpdateEvent(), "partial_update"):
                update = data.update.value
                if not isinstance(update, str):
                    update = update.get_text_content()

                if data.update.key == "final_answer":
                    final_answer += update

                yield Message(
                    message_id=str(uuid.uuid4()),
                    task_id=context.task_id,
                    context_id=context.context_id,
                    role=Role.agent,
                    parts=[Part(root=TextPart(text=update))],
                    metadata={"update_kind": data.update.key},
                )

    messages[context.context_id].append(AssistantMessage(final_answer))


def serve():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 10000)))


if __name__ == "__main__":
    serve()
