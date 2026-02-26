# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from __future__ import annotations

import uuid
from types import NoneType
from typing import TYPE_CHECKING, Annotated, Any, Literal

import a2a.types
from mcp import Implementation, Tool
from opentelemetry import trace
from pydantic import BaseModel, Discriminator, Field, TypeAdapter

from agentstack_sdk.a2a.extensions.base import BaseExtensionClient, BaseExtensionServer, BaseExtensionSpec
from agentstack_sdk.a2a.types import AgentMessage, InputRequired
from agentstack_sdk.util.pydantic import REDACT_SECRETS, REVEAL_SECRETS, SecureBaseModel
from agentstack_sdk.util.telemetry import flatten_dict

__all__ = [
    "A2A_EXTENSION_APPROVAL_REQUESTED",
    "A2A_EXTENSION_APPROVAL_RESOLVED",
    "ApprovalExtensionClient",
    "ApprovalExtensionMetadata",
    "ApprovalExtensionParams",
    "ApprovalExtensionServer",
    "ApprovalExtensionSpec",
    "ApprovalRejectionError",
    "ApprovalRequest",
    "ApprovalResponse",
    "GenericApprovalRequest",
    "ToolCallApprovalRequest",
    "ToolCallServer",
]

if TYPE_CHECKING:
    from agentstack_sdk.server.context import RunContext


A2A_EXTENSION_APPROVAL_REQUESTED = "a2a_extension.approval.requested"
A2A_EXTENSION_APPROVAL_RESOLVED = "a2a_extension.approval.resolved"


class ApprovalRejectionError(RuntimeError):
    pass


class GenericApprovalRequest(SecureBaseModel):
    action: Literal["generic"] = "generic"

    title: str | None = Field(None, description="A human-readable title for the action being approved.")
    description: str | None = Field(None, description="A human-readable description of the action being approved.")


class ToolCallServer(SecureBaseModel):
    name: str = Field(description="The programmatic name of the server.")
    title: str | None = Field(description="A human-readable title for the server.")
    version: str = Field(description="The version of the server.")


class ToolCallApprovalRequest(SecureBaseModel):
    action: Literal["tool-call"] = "tool-call"

    title: str | None = Field(None, description="A human-readable title of the tool.")
    description: str | None = Field(None, description="A human-readable description of the tool.")
    name: str = Field(description="The programmatic name of the tool.")
    input: dict[str, Any] | None = Field(description="The input for the tool.")
    server: ToolCallServer | None = Field(None, description="The server executing the tool.")

    @staticmethod
    def from_mcp_tool(
        tool: Tool, input: dict[str, Any] | None, server: Implementation | None = None
    ) -> "ToolCallApprovalRequest":
        return ToolCallApprovalRequest(
            name=tool.name,
            title=tool.annotations.title if tool.annotations else None,
            description=tool.description,
            input=input,
            server=ToolCallServer(name=server.name, title=server.title, version=server.version) if server else None,
        )


ApprovalRequest = Annotated[GenericApprovalRequest | ToolCallApprovalRequest, Discriminator("action")]


class ApprovalResponse(SecureBaseModel):
    decision: Literal["approve", "reject"]

    @property
    def approved(self) -> bool:
        return self.decision == "approve"

    def raise_on_rejection(self) -> None:
        if self.decision == "reject":
            raise ApprovalRejectionError("Approval request has been rejected")


class ApprovalExtensionParams(BaseModel):
    pass


class ApprovalExtensionSpec(BaseExtensionSpec[ApprovalExtensionParams]):
    URI: str = "https://a2a-extensions.agentstack.beeai.dev/interactions/approval/v1"


class ApprovalExtensionMetadata(BaseModel):
    pass


class ApprovalExtensionServer(BaseExtensionServer[ApprovalExtensionSpec, ApprovalExtensionMetadata]):
    def create_request_message(self, *, request: ApprovalRequest):
        return AgentMessage(
            text="Approval requested",
            metadata={self.spec.URI: request.model_dump(mode="json", context={REVEAL_SECRETS: True})},
        )

    def parse_response(self, *, message: a2a.types.Message):
        if not message.metadata or not (data := message.metadata.get(self.spec.URI)):
            raise ValueError("Approval response data is missing")
        return ApprovalResponse.model_validate(data)

    async def request_approval(
        self,
        request: ApprovalRequest,
        *,
        context: RunContext,
    ) -> ApprovalResponse:
        span = trace.get_current_span()
        span.add_event(
            A2A_EXTENSION_APPROVAL_REQUESTED,
            attributes=flatten_dict(request.model_dump(context={REDACT_SECRETS: True})),
        )
        message = self.create_request_message(request=request)
        message = await context.yield_async(InputRequired(message=message))
        if not message:
            raise RuntimeError("Yield did not return a message")
        response = self.parse_response(message=message)
        span.add_event(
            A2A_EXTENSION_APPROVAL_RESOLVED,
            attributes=flatten_dict(response.model_dump(context={REDACT_SECRETS: True})),
        )
        return response


class ApprovalExtensionClient(BaseExtensionClient[ApprovalExtensionSpec, NoneType]):
    def create_response_message(self, *, response: ApprovalResponse, task_id: str | None):
        return a2a.types.Message(
            message_id=str(uuid.uuid4()),
            role=a2a.types.Role.user,
            parts=[],
            task_id=task_id,
            metadata={self.spec.URI: response.model_dump(mode="json", context={REVEAL_SECRETS: True})},
        )

    def parse_request(self, *, message: a2a.types.Message):
        if not message.metadata or not (data := message.metadata.get(self.spec.URI)):
            raise ValueError("Approval request data is missing")
        return TypeAdapter(ApprovalRequest).validate_python(data)

    def metadata(self) -> dict[str, Any]:
        return {self.spec.URI: ApprovalExtensionMetadata().model_dump(mode="json", context={REVEAL_SECRETS: True})}
