# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import uuid
from types import NoneType
from typing import TYPE_CHECKING, Any, Literal

import a2a.types
import pydantic

from agentstack_sdk.a2a.extensions.base import BaseExtensionClient, BaseExtensionServer, BaseExtensionSpec
from agentstack_sdk.a2a.types import AgentMessage

if TYPE_CHECKING:
    from agentstack_sdk.server.context import RunContext


class ToolCallApprovalRequest(pydantic.BaseModel):
    name: str
    arguments: dict[str, Any] | None = None


class ToolCallApprovalResponse(pydantic.BaseModel):
    action: Literal["accept", "reject"]


class MCPExtensionParams(pydantic.BaseModel):
    pass


class MCPExtensionSpec(BaseExtensionSpec[MCPExtensionParams]):
    URI: str = "https://a2a-extensions.agentstack.beeai.dev/mcp/v1"


class MCPExtensionMetadata(pydantic.BaseModel):
    pass


class MCPExtensionServer(BaseExtensionServer[MCPExtensionSpec, MCPExtensionMetadata]):
    def create_message(self, *, request: ToolCallApprovalRequest):
        return AgentMessage(
            text="Tool call approval requested", metadata={self.spec.URI: request.model_dump(mode="json")}
        )

    def parse_message(self, *, message: a2a.types.Message):
        if not message or not message.metadata or not (data := message.metadata.get(self.spec.URI)):
            raise RuntimeError("Invalid mcp response")
        return ToolCallApprovalResponse.model_validate(data)

    async def raise_tool_approval(self, request: ToolCallApprovalRequest, context: RunContext):
        message = self.create_message(request=request)
        message = await context.yield_async(message)
        if message:
            result = self.parse_message(message=message)
            if result.action != "accept":
                raise RuntimeError("User has rejected the tool call")
        else:
            raise RuntimeError("Tool call approval response is missing")


class MCPExtensionClient(BaseExtensionClient[MCPExtensionSpec, NoneType]):
    def create_message(self, *, response: ToolCallApprovalResponse, task_id: str | None):
        return a2a.types.Message(
            message_id=str(uuid.uuid4()),
            role=a2a.types.Role.user,
            parts=[],
            task_id=task_id,
            metadata={self.spec.URI: response.model_dump(mode="json")},
        )

    def parse_message(self, *, message: a2a.types.Message):
        if not message or not message.metadata or not (data := message.metadata.get(self.spec.URI)):
            raise ValueError("Invalid mcp request")
        return ToolCallApprovalRequest.model_validate(data)
