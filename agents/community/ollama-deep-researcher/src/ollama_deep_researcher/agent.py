import os
from textwrap import dedent
from typing import AsyncIterator

from acp_sdk import Annotations, Metadata, Message, Link, LinkType, MessagePart, PlatformUIAnnotation
from acp_sdk.models.platform import PlatformUIType
from acp_sdk.server import Server
from openinference.instrumentation.langchain import LangChainInstrumentor
from pydantic import AnyUrl

from ollama_deep_researcher.graph import graph
from ollama_deep_researcher.state import SummaryStateInput

LangChainInstrumentor().instrument()

server = Server()


@server.agent(
    metadata=Metadata(
        annotations=Annotations(
            beeai_ui=PlatformUIAnnotation(
                ui_type=PlatformUIType.HANDSOFF,
                user_greeting="What topic do you want to research?",
                display_name="Ollama Deep Researcher",
            ),
        ),
        programming_language="Python",
        license="Apache 2.0",
        framework="LangGraph",
        links=[
            Link(
                type=LinkType.SOURCE_CODE,
                url=AnyUrl(
                    f"https://github.com/i-am-bee/beeai-platform/blob/{os.getenv('RELEASE_VERSION', 'main')}"
                    "/agents/community/ollama-deep-researcher"
                ),
            )
        ],
        documentation=dedent(
            """\
            This agent automates deep web research by generating queries, gathering relevant sources, summarizing key information, and iterating on knowledge gaps to refine the results. It enables structured, efficient research through a configurable workflow.

            ## How It Works
            The agent follows a structured workflow to perform iterative web research and summarization:

            - **Query Generation**: Uses an LLM to generate a precise search query based on the given research topic.
            - **Web Research**: Searches the web using different APIs (Tavily, Perplexity, DuckDuckGo) to retrieve relevant sources.
            - **Summarization**: Extracts key insights from search results and integrates them into an evolving summary.
            - **Reflection & Iteration**: Identifies knowledge gaps and generates follow-up queries for deeper research.
            - **Finalization**: Consolidates all gathered insights and sources into a structured summary.

            The agent loops through steps 2–4 until the research loop limit is reached.

            ## Input Parameters
            - **prompt** (string) – The topic to research.

            ## Key Features
            - **Iterative Research Process** – Automatically refines queries and expands knowledge.
            - **Multi-Source Information Gathering** – Supports Tavily, DuckDuckGo, and Perplexity APIs.
            - **LLM-Powered Summarization** – Generates coherent and well-structured summaries.
            - **Automated Query Refinement** – Identifies knowledge gaps and adjusts queries dynamically.
            """,
        ),
        use_cases=[
            "**Market Research** – Automates data gathering for competitive analysis.",
            "**Academic Research** – Summarizes recent findings on a specific topic.",
            "**Content Creation** – Gathers background information for articles, blogs, and reports.",
            "**Technical Deep Dives** – Explores emerging technologies with structured, iterative research.",
        ],
        env=[
            {"name": "LLM_MODEL", "description": "Model to use from the specified OpenAI-compatible API."},
            {"name": "LLM_API_BASE", "description": "Base URL for OpenAI-compatible API endpoint"},
            {"name": "LLM_API_KEY", "description": "API key for OpenAI-compatible API endpoint"},
        ],
    )
)
async def ollama_deep_researcher(input: list[Message]) -> AsyncIterator:
    """
    The agent performs AI-driven research by generating queries, gathering web data, summarizing findings, and refining
    results through iterative knowledge gap analysis.
    """
    input = SummaryStateInput(research_topic=input[-1].parts[-1].content)
    try:
        output = None
        async for event in graph.astream(input, stream_mode="updates"):
            yield {
                "message": "\n".join(
                    f"🚶‍♂️{key}: {str(value)[:100] + '...' if len(str(value)) > 100 else str(value)}"
                    for key, value in event.items()
                )
                + "\n"
            }
            output = event
        output = output.get("finalize_summary", {}).get("running_summary", None)
        yield MessagePart(content=str(output))
    except Exception as e:
        raise Exception(f"An error occurred while running the graph: {e}")


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    run()
