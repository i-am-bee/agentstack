# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import os
from typing import Annotated, Any

from a2a.types import (
    Message,
    TextPart,
)
from agentstack_sdk.a2a.extensions.interactions.approval import (
    ApprovalExtensionParams,
    ApprovalExtensionServer,
    ApprovalExtensionSpec,
    ToolCallApprovalRequest,
)
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext
from beeai_framework.adapters.mcp.serve.server import _tool_factory
from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.agents.requirement.requirements.ask_permission import AskPermissionRequirement
from beeai_framework.backend import ChatModel
from beeai_framework.tools import AnyTool
from beeai_framework.tools.think import ThinkTool

server = Server()


@server.agent()
async def basic_approve_example(
    input: Message,
    context: RunContext,
    approval_ext: Annotated[ApprovalExtensionServer, ApprovalExtensionSpec(params=ApprovalExtensionParams())],
):
    async def handler(tool: AnyTool, input: dict[str, Any]) -> bool:

        response = await approval_ext.request_approval(
            # using MCP Tool data model as intermediary to simplify conversion
            ToolCallApprovalRequest.from_mcp_tool(_tool_factory(tool), input=input),
            context=context,
        )
        return response.approved

    think_tool = ThinkTool()
    agent = RequirementAgent(
        llm=ChatModel.from_name(os.getenv("LLM_MODEL", "ollama:gpt-oss:20b")),
        tools=[think_tool],
        requirements=[AskPermissionRequirement([think_tool], handler=handler)],
    )

    result = await agent.run("".join(part.root.text for part in input.parts if isinstance(part.root, TextPart)))
    yield result.output[0].text


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    run()
