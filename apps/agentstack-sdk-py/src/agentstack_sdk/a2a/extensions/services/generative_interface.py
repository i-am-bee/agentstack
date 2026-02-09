# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from a2a.server.agent_execution.context import RequestContext
from a2a.types import Message as A2AMessage
from pydantic import BaseModel, Field
from typing_extensions import override

from agentstack_sdk.a2a.extensions.base import (
    BaseExtensionClient,
    BaseExtensionServer,
    BaseExtensionSpec,
)
from agentstack_sdk.a2a.types import AgentMessage, InputRequired

if TYPE_CHECKING:
    from agentstack_sdk.server.context import RunContext


class UIElement(BaseModel):
    key: str
    type: str
    props: dict[str, Any] = Field(default_factory=dict)
    children: list[str] = Field(default_factory=list)


class GenerativeInterfaceSpec(BaseModel):
    root: str
    elements: dict[str, UIElement]


class GenerativeInterfaceResponse(BaseModel):
    component_id: str
    event_type: str
    payload: dict[str, Any] | None = None


class GenerativeInterfaceFulfillments(BaseModel):
    catalog_prompt: str


class GenerativeInterfaceExtensionMetadata(BaseModel):
    generative_interface_fulfillments: GenerativeInterfaceFulfillments | None = None



class FoobarParams(BaseModel):
    foobar: str

class GenerativeInterfaceExtensionSpec(BaseExtensionSpec[FoobarParams]):
    URI: str = "https://a2a-extensions.agentstack.beeai.dev/services/generative_interface/v1"

    @classmethod
    def demand(cls) -> Self:
        return cls(params=FoobarParams(foobar="xxx"))


class GenerativeInterfaceExtensionServer(
    BaseExtensionServer[GenerativeInterfaceExtensionSpec, GenerativeInterfaceExtensionMetadata]
):
    @override
    def handle_incoming_message(self, message: A2AMessage, run_context: RunContext, request_context: RequestContext):
        super().handle_incoming_message(message, run_context, request_context)
        self.context = run_context

    @property
    def catalog_prompt(self) -> str | None:
        if self.data and self.data.generative_interface_fulfillments:
            return self.data.generative_interface_fulfillments.catalog_prompt
        return None

    async def request_ui(self, *, spec: GenerativeInterfaceSpec) -> GenerativeInterfaceResponse | None:
        message = await self.context.yield_async(
            InputRequired(message=AgentMessage(metadata={self.spec.URI: spec.model_dump()}))
        )
        if not message:
            return None
        response_data = message.metadata.get(self.spec.URI) if message.metadata else None
        if not response_data:
            return None
        return GenerativeInterfaceResponse.model_validate(response_data)


class GenerativeInterfaceExtensionClient(
    BaseExtensionClient[GenerativeInterfaceExtensionSpec, GenerativeInterfaceSpec]
): ...
