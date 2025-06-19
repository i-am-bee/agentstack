import os
from textwrap import dedent

from acp_sdk import Annotations, MessagePart, Metadata, Link, LinkType, PlatformUIAnnotation
from acp_sdk.models.platform import PlatformUIType
from crewai import LLM
from acp_sdk.server import Server, Context
from acp_sdk.models import Message
from typing import Iterator, Any
from openinference.instrumentation.crewai import CrewAIInstrumentor
from crewai.agents.parser import AgentAction, AgentFinish
from pydantic import AnyUrl

from marketing_strategy.crew import create_marketing_crew

CrewAIInstrumentor().instrument()

server = Server()


@server.agent(
    metadata=Metadata(
        annotations=Annotations(
            beeai_ui=PlatformUIAnnotation(
                ui_type=PlatformUIType.HANDSOFF,
                user_greeting="What topic do you want to create a marketing strategy around?",
            ),
        ),
        programming_language="Python",
        links=[
            Link(
                type=LinkType.SOURCE_CODE,
                url=AnyUrl(
                    f"https://github.com/i-am-bee/beeai-platform/blob/{os.getenv('RELEASE_VERSION', 'main')}"
                    "/agents/community/marketing-strategy"
                ),
            )
        ],
        framework="CrewAI",
        documentation=dedent(
            """\
            The agent conducts in-depth marketing strategy analysis for projects by leveraging a coordinated crew of
            agents with specific roles. It breaks down the process into sequential tasks, each handled by specialized 
            agents such as the Lead Market Analyst, Chief Marketing Strategist, and Creative Content Creator. This 
            approach ensures that the final output is a well-rounded and actionable marketing strategy tailored to the 
            project's needs.

            ## How It Works
            The agent initializes a server where it registers a "marketing-strategy" agent, which analyzes projects by 
            executing a series of tasks. Each task is managed by a specific agent, with their outputs feeding into 
            subsequent tasks. The Lead Market Analyst conducts initial research, the Chief Marketing Strategist 
            formulates strategies, and the Creative Content Creator develops campaign ideas and marketing copies. 
            The process is executed asynchronously to enhance performance and efficiency.

            ## Input Parameters
            - **text** (string) – A text which describes the project for which the marketing strategy is to be developed.

            ## Key Features
            - **Multi-Agent Coordination** – Utilizes multiple specialized agents to perform distinct tasks in the 
            marketing strategy process.
            - **Sequential Task Execution** – The agents execute tasks in a predefined order to ensure comprehensive 
            strategy formulation.
            - **Asynchronous Processing** – Enhances efficiency by running tasks asynchronously within the framework.
            """
        ),
        use_cases=[
            "**Marketing Strategy Development** – Ideal for businesses needing a comprehensive marketing plan for new projects or campaigns.",
            "**Campaign Ideation** – Generates innovative and engaging campaign ideas aligned with marketing strategies.",
            "**Copy Creation** – Develops compelling marketing copies tailored to specific campaign ideas and target audiences.",
        ],
        license="Apache 2.0",
        env=[
            {"name": "LLM_MODEL", "description": "Model to use from the specified OpenAI-compatible API."},
            {"name": "LLM_API_BASE", "description": "Base URL for OpenAI-compatible API endpoint"},
            {"name": "LLM_API_KEY", "description": "API key for OpenAI-compatible API endpoint"},
        ],
    )
)
def marketing_strategy(input: list[Message], context: Context) -> Iterator:
    """
    The agent performs comprehensive marketing strategy analysis for projects, generating detailed strategies,
    campaign ideas, and compelling marketing copies through a structured process involving multiple expert roles.
    """
    llm = LLM(
        model=f"openai/{os.getenv('LLM_MODEL', 'llama3.1')}",
        base_url=os.getenv("LLM_API_BASE", "http://localhost:11434/v1"),
        api_key=os.getenv("LLM_API_KEY", "dummy"),
    )

    def step_callback(event: Any, *args, **kwargs) -> None:
        match event:
            case AgentAction():
                context.yield_sync(
                    {
                        "thought": event.thought,
                        "tool": event.tool,
                        "tool_input": event.tool_input,
                        "result": event.result,
                    }
                )
            case AgentFinish():
                context.yield_sync({"output": event.output})
            case _:
                return  # unsupported event

    try:
        input = {"project_description": input[-1].parts[-1].content}
        result = create_marketing_crew(llm, step_callback).kickoff(inputs=input)
        yield MessagePart(content=result.raw)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    run()
