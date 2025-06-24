import os
from textwrap import dedent
from typing import Any

from acp_sdk import (
    Annotations,
    AnyUrl,
    Link,
    LinkType,
    Message,
    MessagePart,
    Metadata,
    PlatformUIAnnotation,
)
from acp_sdk.models.platform import PlatformUIType

from gpt_researcher import GPTResearcher

from acp_sdk.server import Context, Server

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
                    "/agents/community/gpt-researcher"
                ),
            )
        ],
        documentation=dedent(
            """\
            The agent is an autonomous system designed to perform detailed research on any specified topic, leveraging both web and local resources. It generates a long, factual report complete with citations, striving to provide unbiased and accurate information. Drawing inspiration from recent advancements in AI-driven research methodologies, the agent addresses common challenges like misinformation and the limits of traditional LLMs, offering robust performance through parallel processing.

            ## How It Works
            The GPT Researcher agent operates by deploying a 'planner' to generate relevant research questions and 'execution' agents to collect information. The system then aggregates these findings into a well-structured report. This approach minimizes biases by cross-referencing multiple sources and focuses on delivering comprehensive insights. It employs a custom infrastructure to ensure rapid and deterministic outcomes, making it suitable for diverse research applications.

            ## Input Parameters
            - **text** (string) – The topic or query for which the research report is to be generated.

            ## Key Features
            - **Comprehensive Research** – Generates detailed reports using information from multiple sources.
            - **Bias Reduction** – Cross-references data from various platforms to minimize misinformation and bias.
            - **High Performance** – Utilizes parallelized processes for efficient and swift report generation.
            - **Customizable** – Offers customization options to tailor research for specific domains or tasks.
            """
        ),
        use_cases=[
            "**Comprehensive Research** – Generates detailed reports using information from multiple sources.",
            "**Bias Reduction** – Cross-references data from various platforms to minimize misinformation and bias.",
            "**High Performance** – Utilizes parallelized processes for efficient and swift report generation.",
            "**Customizable** – Offers customization options to tailor research for specific domains or tasks.",
        ],
        env=[
            {"name": "LLM_MODEL", "description": "Model to use from the specified OpenAI-compatible API."},
            {"name": "LLM_API_BASE", "description": "Base URL for OpenAI-compatible API endpoint"},
            {"name": "LLM_API_KEY", "description": "API key for OpenAI-compatible API endpoint"},
            {"name": "LLM_MODEL_FAST", "description": "Fast model to use from the specified OpenAI-compatible API."},
            {"name": "LLM_MODEL_SMART", "description": "Smart model to use from the specified OpenAI-compatible API."},
            {
                "name": "LLM_MODEL_STRATEGIC",
                "description": "Strategic model to use from the specified OpenAI-compatible API.",
            },
            {"name": "EMBEDDING_MODEL", "description": "Embedding model to use (see GPT Researcher docs for details)"},
        ],
    )
)
async def gpt_researcher(input: list[Message], context: Context) -> None:
    """
    The agent conducts in-depth local and web research using a language model to generate comprehensive reports with
    citations, aimed at delivering factual, unbiased information.
    """
    os.environ["RETRIEVER"] = "duckduckgo"
    os.environ["OPENAI_BASE_URL"] = os.getenv("LLM_API_BASE", "http://localhost:11434/v1")
    os.environ["OPENAI_API_KEY"] = os.getenv("LLM_API_KEY", "dummy")
    model = os.getenv("LLM_MODEL", "llama3.1")
    os.environ["LLM_MODEL"] = model
    os.environ["FAST_LLM"] = f"openai:{os.getenv('LLM_MODEL_FAST', model)}"
    os.environ["SMART_LLM"] = f"openai:{os.getenv('LLM_MODEL_SMART', model)}"
    os.environ["STRATEGIC_LLM"] = f"openai:{os.getenv('LLM_MODEL_STRATEGIC', model)}"

    embedding_model = os.getenv("EMBEDDING_MODEL")
    if embedding_model:
        os.environ["EMBEDDING"] = embedding_model

    class CustomLogsHandler:
        async def send_json(self, data: dict[str, Any]) -> None:
            if "output" not in data:
                return
            match data.get("type"):
                case "logs":
                    await context.yield_async({"message": f"{data['output']}\n"})
                case "report":
                    await context.yield_async(MessagePart(content=data["output"]))

    researcher = GPTResearcher(query=str(input[-1]), report_type="research_report", websocket=CustomLogsHandler())
    await researcher.conduct_research()
    await researcher.write_report()


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    run()
