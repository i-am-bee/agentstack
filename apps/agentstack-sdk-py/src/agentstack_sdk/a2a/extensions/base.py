# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from __future__ import annotations

import abc
import typing
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from contextvars import ContextVar
from types import NoneType
from typing import Self

import pydantic
from a2a.server.agent_execution.context import RequestContext
from a2a.types import AgentCard, AgentExtension
from a2a.types import Message as A2AMessage
from google.protobuf.json_format import MessageToDict
from opentelemetry import trace
from opentelemetry.trace import SpanKind
from pydantic import BaseModel
from typing_extensions import override

from agentstack_sdk.util.pydantic import REDACT_SECRETS
from agentstack_sdk.util.telemetry import (
    flatten_dict,
    trace_class,
)

ParamsT = typing.TypeVar("ParamsT")
MetadataFromClientT = typing.TypeVar("MetadataFromClientT")
MetadataFromServerT = typing.TypeVar("MetadataFromServerT")


if typing.TYPE_CHECKING:
    from agentstack_sdk.server.context import RunContext


A2A_EXTENSION_URI = "a2a_extension.uri"
A2A_EXTENSION_METADATA_RECEIVED_EVENT = "a2a_extension.metadata.received"


def _get_generic_args(cls: type, base_class: type) -> tuple[typing.Any, ...]:
    for base in getattr(cls, "__orig_bases__", ()):
        if typing.get_origin(base) is base_class and (args := typing.get_args(base)):
            return args
    raise TypeError(f"Missing Params type for {cls.__name__}")


class BaseExtensionSpec(abc.ABC, typing.Generic[ParamsT]):
    """
    Base class for an A2A extension handler.

    The base implementations assume a single URI. More complex extension
    handlers (e.g. serving multiple versions of an extension spec) may override
    the appropriate methods.
    """

    URI: str
    """
    URI of the extension spec, or the preferred one if there are multiple supported.
    """

    DESCRIPTION: str | None = None
    """
    Description to be attached with the extension spec.
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.Params = _get_generic_args(cls, BaseExtensionSpec)[0]

    params: ParamsT
    """
    Params from the agent card.
    """

    def __init__(self, params: ParamsT, required: bool = False) -> None:
        """
        Agent should construct an extension instance using the constructor.
        """
        self.params = params
        self.required = required

    @classmethod
    def from_agent_card(cls: type[typing.Self], agent: AgentCard) -> typing.Self | None:
        """
        Client should construct an extension instance using this classmethod.
        """
        if extensions := [x for x in agent.capabilities.extensions or [] if x.uri == cls.URI]:
            return cls(params=pydantic.TypeAdapter(cls.Params).validate_python(MessageToDict(extensions[0].params)))
        return None

    def to_agent_card_extensions(self, *, required: bool | None = None) -> list[AgentExtension]:
        """
        Agent should use this method to obtain extension definitions to advertise on the agent card.
        This returns a list, as it's possible to support multiple A2A extensions within a single class.
        (Usually, that would be different versions of the extension spec.)
        """
        return [
            AgentExtension(
                uri=self.URI,
                description=self.DESCRIPTION,
                params=typing.cast(
                    dict[str, typing.Any] | None,
                    pydantic.TypeAdapter(self.Params).dump_python(self.params, mode="json"),
                ),
                required=required if required is not None else self.required,
            )
        ]


class NoParamsBaseExtensionSpec(BaseExtensionSpec[NoneType]):
    def __init__(self, required: bool = False):
        super().__init__(None, required)

    @classmethod
    @override
    def from_agent_card(cls, agent: AgentCard) -> typing.Self | None:
        if extensions := [e for e in agent.capabilities.extensions or [] if e.uri == cls.URI]:
            return cls(required=extensions[0].required or False)
        return None


ExtensionSpecT = typing.TypeVar("ExtensionSpecT", bound=BaseExtensionSpec[typing.Any])


class BaseExtensionServer(abc.ABC, typing.Generic[ExtensionSpecT, MetadataFromClientT]):
    """
    Type of the extension metadata, attached to messages.
    """

    def __init_subclass__(cls: type[Self], **kwargs):
        super().__init_subclass__(**kwargs)

        generic_args = _get_generic_args(cls, BaseExtensionServer)
        trace_class(
            kind=SpanKind.SERVER,
            exclude_list=["lifespan", "_fork"],
            attributes={A2A_EXTENSION_URI: generic_args[0].URI},
        )(cls)
        cls.MetadataFromClient = generic_args[1]
        cls._context_var = ContextVar(f"extension_{cls.__name__}", default=None)

    _metadata_from_client: MetadataFromClientT | None = None

    @classmethod
    def current(cls) -> Self | None:
        return cls._context_var.get()

    @property
    def data(self) -> MetadataFromClientT | None:
        return self._metadata_from_client

    def __bool__(self):
        return bool(self.data)

    def __init__(self, spec: ExtensionSpecT, *args, **kwargs) -> None:
        self.spec = spec
        self._args = args
        self._kwargs = kwargs

    def parse_client_metadata(self, message: A2AMessage) -> MetadataFromClientT | None:
        """
        Server should use this method to retrieve extension-associated metadata from a message.
        """
        metadata = MessageToDict(message.metadata)
        return (
            None
            if not metadata or self.spec.URI not in metadata
            else pydantic.TypeAdapter(self.MetadataFromClient).validate_python(metadata[self.spec.URI])
        )

    def handle_incoming_message(self, message: A2AMessage, run_context: RunContext, request_context: RequestContext):
        if self._metadata_from_client is None:
            self._metadata_from_client = self.parse_client_metadata(message)
            if isinstance(self._metadata_from_client, BaseModel):
                trace.get_current_span().add_event(
                    A2A_EXTENSION_METADATA_RECEIVED_EVENT,
                    attributes=flatten_dict(self._metadata_from_client.model_dump(context={REDACT_SECRETS: True})),
                )

    def _fork(self) -> typing.Self:
        """Creates a clone of this instance with the same arguments as the original"""
        return type(self)(self.spec, *self._args, **self._kwargs)

    def __call__(self, message: A2AMessage, run_context: RunContext, request_context: RequestContext) -> typing.Self:
        """Works as a dependency constructor - create a private instance for the request"""
        instance = self._fork()
        instance._context_var.set(instance)  # type: ignore
        instance.handle_incoming_message(message, run_context, request_context)
        return instance

    @asynccontextmanager
    async def lifespan(self) -> AsyncIterator[None]:
        """Called when entering the agent context after the first message was parsed (__call__ was already called)"""
        yield


class BaseExtensionClient(abc.ABC, typing.Generic[ExtensionSpecT, MetadataFromServerT]):
    """
    Type of the extension metadata, attached to messages.
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        generic_args = _get_generic_args(cls, BaseExtensionClient)
        trace_class(kind=SpanKind.CLIENT, attributes={A2A_EXTENSION_URI: generic_args[0].URI})(cls)
        cls.MetadataFromServer = generic_args[1]

    def __init__(self, spec: ExtensionSpecT) -> None:
        self.spec = spec

    def parse_server_metadata(self, message: A2AMessage) -> MetadataFromServerT | None:
        """
        Client should use this method to retrieve extension-associated metadata from a message.
        """
        return (
            None
            if not message.metadata or self.spec.URI not in message.metadata
            else pydantic.TypeAdapter(self.MetadataFromServer).validate_python(
                MessageToDict(message.metadata)[self.spec.URI]
            )
        )
