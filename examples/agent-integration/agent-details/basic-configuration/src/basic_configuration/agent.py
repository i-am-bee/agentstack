# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from textwrap import dedent

from a2a.types import AgentSkill, Message
from agentstack_sdk.a2a.extensions import AgentDetail, AgentDetailContributor, AgentDetailTool
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext

server = Server()


@server.agent(
    name="Example Research Assistant",
    detail=AgentDetail(
        interaction_mode="multi-turn",  # or single-turn
        user_greeting="Hi there! I can help you research topics or summarize uploaded documents.",
        tools=[
            AgentDetailTool(name="Web Search", description="Looks up recent and relevant information from the web."),
            AgentDetailTool(
                name="Document Reader", description="Reads and extracts key insights from uploaded PDFs or text files."
            ),
        ],
        framework="BeeAI Framework",
        author=AgentDetailContributor(
            name="Agent Stack Team",
            email="team@example.com",
        ),
        source_code_url="https://github.com/example/example-research-assistant",
    ),
    skills=[
        AgentSkill(
            id="research",
            name="Research",
            description=dedent(
                """\
                Finds up-to-date information on a given topic, synthesizes key points, 
                and summarizes findings in clear, useful responses.
                """
            ),
            tags=["Search", "Knowledge"],
            examples=[
                "Find recent news about AI ethics in 2025.",
                "What are the main challenges in renewable energy adoption?",
                "Give me an overview of current space exploration missions.",
            ],
        ),
        AgentSkill(
            id="summarization",
            name="Summarization",
            description=dedent(
                """\
                Reads and summarizes uploaded text or documents, highlighting the 
                most important ideas, statistics, and conclusions.
                """
            ),
            tags=["Documents", "Summaries"],
            examples=[
                "Summarize this PDF report about electric vehicle trends.",
                "What are the main points from this research article?",
                "Condense this document into a short summary I can share.",
            ],
        ),
    ],
)
async def basic_configuration_example(input: Message, context: RunContext):
    """An example agent with detailed configuration"""
    yield "Hello World!"


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    run()
