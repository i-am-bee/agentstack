# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from sdk import Server
from extensions import BeeAIUITool, AgentDetailsContributor, BeeAIUI
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
        framework="BeeAI",
        license="GPL v3.0",
        programming_language="Python",
        source_code_url="https://github.com/i-am-bee/beeai-platform",
        container_image_url='',
        author=AgentDetailsContributor(name= 'Tomas Weiss', email="Tomas.Weiss@ibm.com", url= "https://research.ibm.com/"),
        contributors=[
            AgentDetailsContributor(name= 'Petr Kadlec', email="petr.kadlec@ibm.com"),
            AgentDetailsContributor(name= 'Petr Bulánek', email="petr.bulanek@ibm.com"),
        ],
        starter_prompts=['Write a research report about Generative AI','Should I buy Apple stock now?','Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolor. This is what a long query would look like, 2 lines maximum. Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolor. This is what a long query would look like, 2 lines maximum...','What is the meaning of life?','Tell me a joke','What is the capital of France?','How do I make a cake?']
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
