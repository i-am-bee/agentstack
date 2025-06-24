from collections.abc import AsyncGenerator
from acp_sdk.models import Message, MessagePart
from acp_sdk.server import Context, RunYield, RunYieldResume, Server
from acp_sdk import Metadata
from textwrap import dedent
import os
from langgraph.checkpoint.memory import MemorySaver
from business_case_assistant.graph import build_graph

memory = MemorySaver()
graph = build_graph()
graph = graph.compile(checkpointer=memory)

server = Server()


@server.agent(
    metadata=Metadata(
        version="1.0.0",
        framework="LangGraph",
        programming_language="Python",
        ui={
            "type": "chat",
            "user_greeting": """To get started, could you please share the key points or objectives of your business case?""",
        },
        author={
            "name": "Caitlin Tran",
        },
        recommended_models=[
            "claude-3-7-sonnet-20250219",
        ],
        env=[
            {"name": "LLM_MODEL", "description": "Model to use from the specified OpenAI-compatible API."},
            {"name": "LLM_API_BASE", "description": "Base URL for OpenAI-compatible API endpoint"},
            {"name": "LLM_API_KEY", "description": "API key for OpenAI-compatible API endpoint"},
        ],
        documentation=dedent(
            """\
            The AI agent uses advanced language models and LangGraph to interview the user about project requirements and 
            create a business case document based on the user's responses.
            
            ## How It Works
            The user enters the key points or objectives of their business case. If the agent needs more information, it will ask the user follow up questions until it 
            has gathered enough information to create a comprehensive business case document. Once it decides that it has gathered enough information,
            a business case document will be generated containing the following sections:
            - Introduction
            - General Project Information
            - High Level Business Impact
            - Alternatives and Analysis
            - Preferred Solution
            - Executive Summary

            ## Key Features
            - **Conversational AI** - Handles multi-turn conversations in order to interview the user about business requirements.
            - **Business Case Generation** - Drafts business case documents based on the business requirements inputted by the user.
            """
        ),
        use_cases=[
            "**Conversational AI** - Handles multi-turn conversations with memory while interviewing the user about business requirements",
            "**Business Case Generation** - Drafts business case documents based on the business requirements inputted by the user",
        ],
    ),
)
async def business_case_assistant(input: list[Message], context: Context) -> AsyncGenerator[RunYield, RunYieldResume]:
    """Interviews the user about project requirements and creates a business case document."""
    message = input[-1].parts[0].content
    config = {"configurable": {"thread_id": context.session_id}}

    async for event in graph.astream({"messages": str(message)}, config, stream_mode="updates"):
        output = event
        print(output)
        node = list(output.keys())[0]
        if node == "Gathering Requirements":
            output = output.get("Gathering Requirements", {}).get("messages", [])
            for msg in output:
                yield MessagePart(content=msg.content)
        elif node == "Compiling Document":
            output = output.get("Compiling Document", {}).get("document", [])
            yield MessagePart(content=output)


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    run()
