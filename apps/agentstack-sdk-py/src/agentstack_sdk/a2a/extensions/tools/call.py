# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import uuid
from types import NoneType
from typing import TYPE_CHECKING, Any, Literal

import a2a.types
from mcp import Tool
from mcp.types import Implementation
from pydantic import BaseModel, Field

from agentstack_sdk.a2a.extensions.base import BaseExtensionClient, BaseExtensionServer, BaseExtensionSpec
from agentstack_sdk.a2a.extensions.tools.exceptions import ToolCallRejectionError
from agentstack_sdk.a2a.types import AgentMessage, InputRequired

if TYPE_CHECKING:
    from agentstack_sdk.server.context import RunContext


class ToolCallServer(BaseModel):
    name: str = Field(description="The programmatic name of the server.")
    title: str | None = Field(description="A human-readable title for the server.")
    version: str = Field(description="The version of the server.")


class ToolCallRequest(BaseModel):
    name: str = Field(description="The programmatic name of the tool.")
    title: str | None = Field(None, description="A human-readable title for the tool.")
    description: str | None = Field(None, description="A human-readable description of the tool.")

    input: dict[str, Any] | None = Field(description="The input for the tool.")

    server: ToolCallServer | None = Field(None, description="The server executing the tool.")

    @staticmethod
    def from_mcp_tool(
        tool: Tool, input: dict[str, Any] | None, server: Implementation | None = None
    ) -> ToolCallRequest:
        return ToolCallRequest(
            name=tool.name,
            title=tool.annotations.title if tool.annotations else None,
            description=tool.description,
            input=input,
            server=ToolCallServer(name=server.name, title=server.title, version=server.version) if server else None,
        )


class ToolCallResponse(BaseModel):
    action: Literal["accept", "reject"]


class ToolCallExtensionParams(BaseModel):
    pass


class ToolCallExtensionSpec(BaseExtensionSpec[ToolCallExtensionParams]):
    URI: str = "https://a2a-extensions.agentstack.beeai.dev/tools/call/v1"


class ToolCallExtensionMetadata(BaseModel):
    pass


class ToolCallExtensionServer(BaseExtensionServer[ToolCallExtensionSpec, ToolCallExtensionMetadata]):
    def create_request_message(self, *, request: ToolCallRequest):
        return AgentMessage(
            text="Tool call approval requested", metadata={self.spec.URI: request.model_dump(mode="json")}
        )

    def parse_response(self, *, message: a2a.types.Message):
        if not message or not message.metadata or not (data := message.metadata.get(self.spec.URI)):
            raise RuntimeError("Invalid mcp response")
        return ToolCallResponse.model_validate(data)

    async def request_tool_call_approval(
        self,
        request: ToolCallRequest,
        *,
        context: RunContext,
    ) -> ToolCallResponse:
        message = self.create_request_message(request=request)
        message = await context.yield_async(InputRequired(message=message))
        if message:
            result = self.parse_response(message=message)
            match result.action:
                case "accept":
                    return result
                case "reject":
                    raise ToolCallRejectionError("User has rejected the tool call")

        else:
            raise RuntimeError("Yield did not return a message")


class ToolCallExtensionClient(BaseExtensionClient[ToolCallExtensionSpec, NoneType]):
    def create_response_message(self, *, response: ToolCallResponse, task_id: str | None):
        return a2a.types.Message(
            message_id=str(uuid.uuid4()),
            role=a2a.types.Role.user,
            parts=[],
            task_id=task_id,
            metadata={self.spec.URI: response.model_dump(mode="json")},
        )

    def parse_request(self, *, message: a2a.types.Message):
        if not message or not message.metadata or not (data := message.metadata.get(self.spec.URI)):
            raise ValueError("Invalid tool call request")
        return ToolCallRequest.model_validate(data)

    def metadata(self) -> dict[str, Any]:
        return {self.spec.URI: ToolCallExtensionMetadata().model_dump(mode="json")}
