# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from __future__ import annotations

import abc
import typing
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from types import NoneType

import pydantic
from a2a.server.agent_execution.context import RequestContext
from a2a.types import AgentCard, AgentExtension
from a2a.types import Message as A2AMessage
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
    from agentstack_sdk.server.dependencies import Dependency


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

    def __init__(self, params: ParamsT) -> None:
        """
        Agent should construct an extension instance using the constructor.
        """
        self.params = params

    @classmethod
    def from_agent_card(cls: type["BaseExtensionSpec"], agent: AgentCard) -> typing.Self | None:
        """
        Client should construct an extension instance using this classmethod.
        """
        try:
            return cls(
                params=pydantic.TypeAdapter(cls.Params).validate_python(
                    next(x for x in agent.capabilities.extensions or [] if x.uri == cls.URI).params
                ),
            )
        except StopIteration:
            return None

    def to_agent_card_extensions(self, *, required: bool = False) -> list[AgentExtension]:
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
                required=required,
            )
        ]


class NoParamsBaseExtensionSpec(BaseExtensionSpec[NoneType]):
    def __init__(self):
        super().__init__(None)

    @classmethod
    @override
    def from_agent_card(cls, agent: AgentCard) -> typing.Self | None:
        if any(e.uri == cls.URI for e in agent.capabilities.extensions or []):
            return cls()
        return None


ExtensionSpecT = typing.TypeVar("ExtensionSpecT", bound=BaseExtensionSpec[typing.Any])


class BaseExtensionServer(abc.ABC, typing.Generic[ExtensionSpecT, MetadataFromClientT]):
    """
    Type of the extension metadata, attached to messages.
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        generic_args = _get_generic_args(cls, BaseExtensionServer)
        trace_class(
            kind=SpanKind.SERVER,
            exclude_list=["lifespan", "_fork"],
            attributes={A2A_EXTENSION_URI: generic_args[0].URI},
        )(cls)
        cls.MetadataFromClient = generic_args[1]

    _metadata_from_client: MetadataFromClientT | None = None
    _dependencies: dict[str, Dependency] = {}  # noqa: RUF012

    @property
    def data(self):
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
        return (
            None
            if not message.metadata or self.spec.URI not in message.metadata
            else pydantic.TypeAdapter(self.MetadataFromClient).validate_python(message.metadata[self.spec.URI])
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

    def __call__(
        self,
        message: A2AMessage,
        run_context: RunContext,
        request_context: RequestContext,
        dependencies: dict[str, Dependency],
    ) -> typing.Self:
        """Works as a dependency constructor - create a private instance for the request"""
        instance = self._fork()
        instance._dependencies = dependencies
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
            else pydantic.TypeAdapter(self.MetadataFromServer).validate_python(message.metadata[self.spec.URI])
        )
