# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, cast

from a2a.types import Message as A2AMessage
from pydantic import TypeAdapter

from agentstack_sdk.a2a.extensions.base import (
    BaseExtensionClient,
    BaseExtensionServer,
    NoParamsBaseExtensionSpec,
)
from agentstack_sdk.a2a.extensions.common.form import FormRender, FormResponse
from agentstack_sdk.a2a.types import AgentMessage, InputRequired

if TYPE_CHECKING:
    from agentstack_sdk.server.context import RunContext

T = TypeVar("T")


class RequestFormExtensionSpec(NoParamsBaseExtensionSpec):
    URI: str = "https://a2a-extensions.agentstack.beeai.dev/ui/request_form/v1"


class RequestFormExtensionServer(BaseExtensionServer[RequestFormExtensionSpec, FormResponse]):
    def handle_incoming_message(self, message: A2AMessage, context: RunContext):
        super().handle_incoming_message(message, context)
        self.context = context

    async def request_form(self, *, form: FormRender, model: type[T] = FormResponse) -> T | None:
        message = await self.context.yield_async(
            InputRequired(message=AgentMessage(text=form.title, metadata={self.spec.URI: form}))
        )
        return self.parse_form_response(message=message, model=model) if message else None

    def parse_form_response(self, *, message: A2AMessage, model: type[T] = FormResponse) -> T | None:
        form_response = self.parse_client_metadata(message)
        if form_response is None:
            return None
        if model is FormResponse:
            return cast(T, form_response)
        return TypeAdapter(model).validate_python(dict(form_response))


class RequestFormExtensionClient(BaseExtensionClient[RequestFormExtensionSpec, FormRender]): ...
