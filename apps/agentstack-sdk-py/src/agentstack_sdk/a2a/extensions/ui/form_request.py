# Copyright 2026 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, overload

from a2a.server.agent_execution.context import RequestContext
from a2a.types import Message as A2AMessage
from pydantic import TypeAdapter
from typing_extensions import override

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


class FormRequestExtensionSpec(NoParamsBaseExtensionSpec):
    URI: str = "https://a2a-extensions.agentstack.beeai.dev/ui/form_request/v1"


class FormRequestExtensionServer(BaseExtensionServer[FormRequestExtensionSpec, FormResponse]):
    @override
    def handle_incoming_message(self, message: A2AMessage, run_context: RunContext, request_context: RequestContext):
        super().handle_incoming_message(message, run_context, request_context)
        self.context = run_context

    @overload
    async def request_form(self, *, form: FormRender, model: None = None) -> FormResponse | None: ...
    @overload
    async def request_form(self, *, form: FormRender, model: type[T]) -> T | None: ...
    async def request_form(self, *, form: FormRender, model: type[T] | None = None) -> T | FormResponse | None:
        message = await self.context.yield_async(
            InputRequired(message=AgentMessage(text=form.title, metadata={self.spec.URI: form}))
        )
        return self.parse_form_response(message=message, model=model or FormResponse) if message else None

    @overload
    def parse_form_response(self, *, message: A2AMessage, model: None = None) -> FormResponse | None: ...
    @overload
    def parse_form_response(self, *, message: A2AMessage, model: type[T]) -> T | None: ...
    def parse_form_response(self, *, message: A2AMessage, model: type[T] | None = None) -> T | FormResponse | None:
        form_response = self.parse_client_metadata(message)
        return (
            # pyrefly: ignore [no-matching-overload]
            TypeAdapter(model).validate_python(dict(form_response))
            if form_response is not None and model is not None
            else form_response
        )


class FormRequestExtensionClient(BaseExtensionClient[FormRequestExtensionSpec, FormRender]): ...
