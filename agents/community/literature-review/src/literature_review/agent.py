import dataclasses
import json
import os
from textwrap import dedent
from typing import AsyncGenerator

from acp_sdk import Annotations, AnyUrl, Link, LinkType, Message, MessagePart, Metadata, PlatformUIAnnotation
from acp_sdk.models.platform import PlatformUIType
from acp_sdk.server import Context, Server
from literature_review.team import team
from autogen_agentchat.messages import BaseChatMessage, BaseAgentEvent
from autogen_agentchat.base import TaskResult

server = Server()


@server.agent(
    metadata=Metadata(
        annotations=Annotations(
            beeai_ui=PlatformUIAnnotation(
                ui_type=PlatformUIType.HANDSOFF,
                user_greeting="What topic do you want to research?",
            ),
        ),
        programming_language="Python",
        links=[
            Link(
                type=LinkType.SOURCE_CODE,
                url=AnyUrl(
                    f"https://github.com/i-am-bee/beeai-platform/blob/{os.getenv('RELEASE_VERSION', 'main')}"
                    "/agents/community/literature-review"
                ),
            )
        ],
        framework="AutoGen",
        license="Apache 2.0",
        use_cases=[
            "**Academic Research** – Supports researchers by automating the initial phase of literature review.",
            "**Report Generation** – Generates structured academic reports for various topics.",
            "**Resource Compilation** – Compiles a list of academic papers and articles relevant to a given topic.",
        ],
        documentation=dedent(
            """\
            The agent is designed to automate the process of conducting literature reviews by gathering, analyzing, and synthesizing information from multiple sources. It uses a combination of Google searches and Arxiv database queries to fetch relevant academic papers and data, subsequently generating a well-formatted report.

            ## How It Works
            The agent handles requests to perform literature reviews. It utilizes a set of assistant agents, including Google and Arxiv search agents, to gather information. Once the data is collected, a report agent synthesizes the information into a structured literature review, ensuring that references are correctly formatted. The process involves a round-robin communication strategy among the participating agents, with a termination condition for task completion.

            ## Input Parameters
            - **text** (string) – Contains the text query or topic for which the literature review is to be conducted.

            ## Key Features
            - **Automated Literature Review** – Conducts thorough searches across Google and Arxiv to gather relevant academic information.
            - **Structured Report Generation** – Compiles and formats the search results into a coherent literature review with proper references.
            - **Multi-Source Data Collection** – Leverages both general web searches and academic databases for comprehensive data gathering.
            - **Dynamic Agent Collaboration** – Uses a round-robin approach to coordinate between search and report agents.
            """
        ),
        env=[
            {"name": "LLM_MODEL", "description": "Model to use from the specified OpenAI-compatible API."},
            {"name": "LLM_API_BASE", "description": "Base URL for OpenAI-compatible API endpoint"},
            {"name": "LLM_API_KEY", "description": "API key for OpenAI-compatible API endpoint"},
            {"name": "GOOGLE_API_KEY", "description": "Google Search API key"},
            {"name": "GOOGLE_SEARCH_ENGINE_ID", "description": "Google Search Engine ID"},
        ],
    ),
)
async def literature_review(input: list[Message], context: Context) -> AsyncGenerator:
    """
    This agent automates deep web research by generating queries, gathering relevant sources, summarizing key
    information, and iterating on knowledge gaps to refine the results.
    """

    def encode_value(value):
        if dataclasses.is_dataclass(value):
            return dataclasses.asdict(value)
        return value

    def serialize_json(value):
        try:
            return json.dumps(value, indent=2, default=encode_value)
        except (TypeError, ValueError):
            return ""

    try:
        async for value in team.run_stream(task=str(input[-1])):
            if isinstance(value, BaseChatMessage) or isinstance(value, BaseAgentEvent):
                action = {
                    "content": value.content,
                    "type": value.type,
                    "source": value.source,
                }

                yield {"message": serialize_json(action)}
            if isinstance(value, TaskResult):
                content = value.messages[-1].content
                yield MessagePart(content=content)

    except Exception as e:
        raise Exception(f"An error occurred while running the agent: {e}")


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    run()
