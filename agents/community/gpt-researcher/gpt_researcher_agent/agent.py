# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from textwrap import dedent
from typing import Annotated, Any, AsyncGenerator

from a2a.types import AgentSkill, Message

from gpt_researcher import GPTResearcher

from gpt_researcher_agent.env_patch import with_local_env

from beeai_sdk.a2a.extensions import (
    TrajectoryExtensionServer,
    TrajectoryExtensionSpec,
    AgentDetail,
    LLMServiceExtensionServer,
    LLMServiceExtensionSpec,
    EmbeddingServiceExtensionServer,
    EmbeddingServiceExtensionSpec,
)
from beeai_sdk.a2a.types import RunYield
from beeai_sdk.server import Server
from beeai_sdk.server.context import RunContext
from gpt_researcher import GPTResearcher

server = Server()


@server.agent(
    name="GPT Researcher",
    documentation_url=(
        f"https://github.com/i-am-bee/beeai-platform/blob/{os.getenv('RELEASE_VERSION', 'main')}"
        "/agents/community/gpt-researcher"
    ),
    detail=AgentDetail(interaction_mode="single-turn", user_greeting="What topic do you want to research?"),
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
    message: Message,
    context: RunContext,
    trajectory: Annotated[TrajectoryExtensionServer, TrajectoryExtensionSpec()],
    llm_ext: Annotated[LLMServiceExtensionServer, LLMServiceExtensionSpec.single_demand()],
    embedding_ext: Annotated[EmbeddingServiceExtensionServer, EmbeddingServiceExtensionSpec.single_demand()],
) -> AsyncGenerator[RunYield, None]:
    """
    The agent conducts in-depth local and web research using a language model to generate comprehensive reports with
    citations, aimed at delivering factual, unbiased information.
    """
    # Set up local environment for this request

    llm_conf, embedding_conf = None, None
    if llm_ext and llm_ext.data:
        [llm_conf] = llm_ext.data.llm_fulfillments.values()

    if embedding_ext and embedding_ext.data:
        [embedding_conf] = embedding_ext.data.embedding_fulfillments.values()

    model = llm_conf.api_model if llm_conf else "dummy"
    embedding_model = embedding_conf.api_model if embedding_conf else "dummy"

    env = {
        "RETRIEVER": "duckduckgo",
        "OPENAI_BASE_URL": llm_conf.api_base if llm_conf else "http://localhost:11434/v1",
        "OPENAI_API_KEY": llm_conf.api_key if llm_conf else "dummy",
        "LLM_MODEL": model,
        "EMBEDDING": f"openai:{embedding_model}",
        "FAST_LLM": f"openai:{model}",
        "SMART_LLM": f"openai:{model}",
    }
    with with_local_env(env):

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
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)), configure_telemetry=True)


if __name__ == "__main__":
    run()
