# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

# pylint: disable=logging-fstring-interpolation

import asyncio
import os
import sys
from textwrap import dedent

import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentExtension,
    AgentSkill,
)

from chat.agent import SUPPORTED_CONTENT_TYPES, ChatAgentExecutor

DEFAULT_LOG_LEVEL = "info"


def main():
    """Command Line Interface to start the Airbnb Agent server."""
    host = os.getenv("HOST", "localhost")
    port = int(os.getenv("PORT", "8000"))
    log_level = os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL)

    async def run_server_async():
        # Initialize AirbnbAgentExecutor with preloaded tools
        agent_executor = ChatAgentExecutor()

        request_handler = DefaultRequestHandler(agent_executor=agent_executor, task_store=InMemoryTaskStore())
        a2a_server = A2AStarletteApplication(agent_card=get_agent_card(host, port), http_handler=request_handler)
        config = uvicorn.Config(app=a2a_server.build(), host=host, port=port, log_level=log_level.lower())
        await uvicorn.Server(config).serve()

    try:
        asyncio.run(run_server_async())
    except RuntimeError as e:
        print(f"RuntimeError in main: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred in main: {e}", file=sys.stderr)
        sys.exit(1)


def get_agent_card(host: str, port: int):
    """Returns the Agent Card for the Currency Agent."""
    capabilities = AgentCapabilities(
        streaming=True,
        pushNotifications=True,
        extensions=[
            AgentExtension(
                uri="beeai_ui",
                params={
                    "ui_type": "chat",
                    "user_greeting": "How can I help you?",
                    "display_name": "Chat",
                    "tools": [
                        {"name": "Web Search (DuckDuckGo)", "description": "Retrieves real-time search results."},
                        {"name": "Wikipedia Search", "description": "Fetches summaries from Wikipedia."},
                        {
                            "name": "Weather Information (OpenMeteo)",
                            "description": "Provides real-time weather updates.",
                        },
                    ],
                },
            )
        ],
    )

    skill = AgentSkill(
        id="chat",
        name="Chat",
        description=dedent(
            """\
            The agent is an AI-powered conversational system with memory, supporting real-time search,
            Wikipedia lookups, and weather updates through integrated tools.
            """
        ),
        tags=["chat"],
        examples=["Please find a room in LA, CA, April 15, 2025, checkout date is april 18, 2 adults"],
    )
    return AgentCard(
        name="Chat Agent",
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
        documentationUrl=(
            f"https://github.com/i-am-bee/beeai-platform/blob/{os.getenv('RELEASE_VERSION', 'main')}"
            "/agents/official/beeai-framework/chat"
        ),
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=SUPPORTED_CONTENT_TYPES,
        defaultOutputModes=SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        skills=[skill],
    )


if __name__ == "__main__":
    main()
