# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from __future__ import annotations

import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Annotated
from datetime import datetime, timezone
from a2a.utils import get_message_text
from deepagents.backends import CompositeBackend, FilesystemBackend
from a2a.types import Message
from langchain_core.runnables import RunnableConfig

from agentstack_sdk.a2a.extensions import (
    AgentDetail,
    AgentDetailContributor,
    LLMServiceExtensionServer,
    LLMServiceExtensionSpec,
    PlatformApiExtensionSpec,
    PlatformApiExtensionServer,
    LLMServiceExtensionParams,
    LLMDemand,
    TrajectoryExtensionServer,
    TrajectoryExtensionSpec,
    EnvVar,
)
from agentstack_sdk.a2a.types import AgentMessage
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext
from langchain_core.messages import HumanMessage, AIMessageChunk, ToolMessage
from deepagents import create_deep_agent, SubAgent

from content_builder.backend import AgentStackBackend
from content_builder.tools import generate_cover, generate_social_image
from content_builder.utils import load_subagents, create_chat_model, to_langchain_messages
from content_builder.tools import web_search

DEFAULT_MODEL = "anthropic:claude-sonnet-4-5-20250929"
AVAILABLE_SUBAGENTS = load_subagents(config_path=Path("./subagents.yaml"), tools={"web_search": web_search})
LLM_BY_AGENT = {
    "default": LLMDemand(suggested=(DEFAULT_MODEL,), description="Default LLM for the root agent"),
    **{
        agent.name: LLMDemand(suggested=(agent.model,), description=f"LLM for subagent '{agent.name}'")
        for agent in AVAILABLE_SUBAGENTS
        if agent.model
    },
}

server = Server()

CURRENT_DIRECTORY = Path(__file__).parent


@server.agent(
    name="Content Creator Agent (Deepagents)",
    documentation_url=f"https://github.com/i-am-bee/agentstack/blob/{os.getenv('RELEASE_VERSION', 'main')}/agents/deepagents_content_builder",
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain", "image/jpeg", "image/png", "text/markdown"],
    description="A content writer for a technology company that creates engaging, informative content that educates readers about AI, software development, and emerging technologies.",
    detail=AgentDetail(
        interaction_mode="multi-turn",
        author=AgentDetailContributor(name="IBM"),
        variables=[
            EnvVar(name="TAVILY_API_KEY", description="API Key for Tavily to do web search", required=True),
            EnvVar(name="GOOGLE_API_KEY", description="API Key for Google Image models", required=True),
        ],
    ),
)
async def content_builder_agent(
    message: Message,
    context: RunContext,
    llm: Annotated[
        LLMServiceExtensionServer,
        LLMServiceExtensionSpec(params=LLMServiceExtensionParams(llm_demands=LLM_BY_AGENT)),
    ],
    trajectory: Annotated[TrajectoryExtensionServer, TrajectoryExtensionSpec()],
    _: Annotated[PlatformApiExtensionServer, PlatformApiExtensionSpec()],
):
    default_llm_config = llm.data.llm_fulfillments.get("default")
    if not default_llm_config:
        yield "No LLM configured!"
        return

    user_message = get_message_text(message).strip()
    if not user_message:
        yield "Please provide a topic or instruction."
        return

    started_at = datetime.now(timezone.utc)
    await context.store(data=message)

    subagents: list[SubAgent] = []
    for sub_agent in AVAILABLE_SUBAGENTS:
        llm_config = llm.data.llm_fulfillments.get(sub_agent.name) or default_llm_config
        sub_agent = sub_agent.to_deepagent_subagent(model=create_chat_model(llm_config))
        subagents.append(sub_agent)

    agent_stack_backend = AgentStackBackend()
    print([f.filename for f in await agent_stack_backend.alist()])
    fs_backend = FilesystemBackend(virtual_mode=True, root_dir=CURRENT_DIRECTORY)

    agent = create_deep_agent(
        model=create_chat_model(default_llm_config),
        memory=[f"{CURRENT_DIRECTORY}/memory/AGENTS.md"],
        skills=[f"{CURRENT_DIRECTORY}/skills/"],
        tools=[generate_cover, generate_social_image],
        subagents=subagents,
        backend=CompositeBackend(
            default=agent_stack_backend,
            routes={f"{CURRENT_DIRECTORY}/memory/": fs_backend, f"{CURRENT_DIRECTORY}/skills/": fs_backend},
        ),
    )

    thread_id = f"session-{context.task_id}"
    history = [message async for message in context.load_history() if isinstance(message, Message) and message.parts]
    lc_messages = [*to_langchain_messages(history), HumanMessage(content=user_message)]
    tool_calls = defaultdict(lambda: {"name": "", "args": ""})

    async for chunk in agent.astream(
        input={"messages": lc_messages},
        config=RunnableConfig(configurable={"thread_id": thread_id}),
        stream_mode=["messages"],
    ):
        node_name, messages = chunk
        if node_name != "messages" or not messages:
            continue

        for last_msg in messages:
            if isinstance(last_msg, AIMessageChunk):
                if (
                    "finish_reason" in last_msg.response_metadata
                    and last_msg.response_metadata["finish_reason"] == "tool_calls"
                ):
                    for _, data in tool_calls.items():
                        tool_call_metadata = trajectory.trajectory_metadata(
                            title=data["name"], content=json.dumps(obj=data["args"])
                        )
                        yield tool_call_metadata
                        await context.store(data=AgentMessage(metadata=tool_call_metadata))
                    tool_calls.clear()

                elif last_msg.tool_call_chunks:
                    for tc in last_msg.tool_call_chunks:
                        tc_id: str | None = tc.get("id")
                        if tc_id:
                            tool_calls[tc_id]["name"] += tc.get("name") or ""
                            tool_calls[tc_id]["args"] += tc.get("args") or ""
                elif last_msg.text:
                    yield AgentMessage(text=last_msg.text)
                    await context.store(AgentMessage(text=last_msg.text))

            elif isinstance(last_msg, ToolMessage) and last_msg.name and last_msg.text:
                tool_message_metadata = trajectory.trajectory_metadata(title=last_msg.name, content=last_msg.text)
                yield tool_message_metadata
                await context.store(data=AgentMessage(metadata=tool_message_metadata))

    updated_files = await agent_stack_backend.alist(order_by="created_at", order="asc", created_after=started_at)
    for updated_file in updated_files:
        yield updated_file.to_file_part()


def serve():
    try:
        server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 10003)), configure_telemetry=True)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    serve()
