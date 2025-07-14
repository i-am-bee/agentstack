# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from extensions import BeeAIUI
from sdk import Server
from extensions import BeeAIUITool
from models import CitationMetadata, TextPart, TrajectoryMetadata
from fastapi.middleware.cors import CORSMiddleware

server = Server()

@server.agent(
    name="hello",
    description="Returns hello world",
    input_content_types=["text/plain"],
    output_content_types=["text/plain", "application/json"],
    ui=BeeAIUI(
        ui_type="chat",
        user_greeting="How can I help you",
        display_name="Hello",
        tools=[
            BeeAIUITool(
                name="Web Search (DuckDuckGo)",
                description="Retrieves real-time search results.",
            ),
            BeeAIUITool(
                name="Wikipedia Search", description="Fetches summaries from Wikipedia."
            ),
            BeeAIUITool(
                name="Weather Information (OpenMeteo)",
                description="Provides real-time weather updates.",
            ),
        ],
    ),
)
async def hello_world(input: list[TextPart]):
    yield TextPart(content="Hello World")
    yield TextPart(
        content="If you are bored, you can try tipping a cow.",
        metadata=CitationMetadata(
            url="https://en.wikipedia.org/wiki/Cow_tipping",
            start_index=30,
            end_index=43,
        ),
    )
    yield TextPart(
        metadata=TrajectoryMetadata(
            message="Let's now see how tools work",
            tool_name="Testing Tool",
            tool_input={"test": "foobar"},
        )
    )


def main():
    server.run()


if __name__ == "__main__":
    main()
31
