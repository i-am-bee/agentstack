# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from textwrap import dedent
from typing import Any, Annotated, AsyncGenerator

from a2a.types import AgentSkill, Message
from gpt_researcher import GPTResearcher


from beeai_sdk.a2a.extensions import TrajectoryExtensionServer, TrajectoryExtensionSpec, AgentDetail
from beeai_sdk.a2a.types import RunYield
from beeai_sdk.server import Server
from beeai_sdk.server.context import Context

server = Server()


@server.agent(
    name="GPT Researcher",
    documentation_url=(
        f"https://github.com/i-am-bee/beeai-platform/blob/{os.getenv('RELEASE_VERSION', 'main')}"
        "/agents/community/gpt-researcher"
    ),
    detail=AgentDetail(
        ui_type="hands-off",
        user_greeting="What topic do you want to research?",
        use_cases=[
            "**Comprehensive Research** – Generates detailed reports using information from multiple sources.",
            "**Bias Reduction** – Cross-references data from various platforms to minimize misinformation and bias.",
            "**High Performance** – Utilizes parallelized processes for efficient and swift report generation.",
            "**Customizable** – Offers customization options to tailor research for specific domains or tasks.",
        ],
    ),
    skills=[
        AgentSkill(
            id="deep_research",
            name="Deep Research",
            description=dedent(
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
            tags=["research"],
        )
    ],
)
async def gpt_researcher(
    message: Message, context: Context, trajectory: Annotated[TrajectoryExtensionServer, TrajectoryExtensionSpec()]
) -> AsyncGenerator[RunYield, None]:
    """
    The agent conducts in-depth local and web research using a language model to generate comprehensive reports with
    citations, aimed at delivering factual, unbiased information.
    """
    os.environ["RETRIEVER"] = "duckduckgo"
    os.environ["OPENAI_BASE_URL"] = os.getenv("LLM_API_BASE", "http://localhost:11434/v1")
    os.environ["OPENAI_API_KEY"] = os.getenv("LLM_API_KEY", "dummy")
    model = os.getenv("LLM_MODEL", "llama3.1")
    os.environ["LLM_MODEL"] = model

    class CustomLogsHandler:
        async def send_json(self, data: dict[str, Any]) -> None:
            if "output" not in data:
                return
            match data.get("type"):
                case "logs":
                    await context.yield_async(
                        trajectory.trajectory_metadata(title="log", content=f"{data['output']}\n")
                    )
                case "report":
                    await context.yield_async(data["output"])

    if not message.parts or not (query := message.parts[-1].root.text):
        yield "Please enter a topic or query."
        return

    researcher = GPTResearcher(query=query, report_type="research_report", websocket=CustomLogsHandler())
    await researcher.conduct_research()
    await researcher.write_report()


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    run()
