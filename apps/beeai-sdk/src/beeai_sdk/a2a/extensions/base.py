# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import abc
import typing
from types import NoneType

import a2a.types
import pydantic

ParamsT = typing.TypeVar("ParamsT")
MetadataFromClientT = typing.TypeVar("MetadataFromClientT")
MetadataFromServerT = typing.TypeVar("MetadataFromServerT")


if typing.TYPE_CHECKING:
    from beeai_sdk.server.context import Context


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

    Params: type[ParamsT]
    """
    Type of the extension params, attached to the agent card.
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
    def from_agent_card(cls, agent: a2a.types.AgentCard) -> typing.Self | None:
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

    def to_agent_card_extensions(self, *, required: bool = False) -> list[a2a.types.AgentExtension]:
        """
        Agent should use this method to obtain extension definitions to advertise on the agent card.
        This returns a list, as it's possible to support multiple A2A extensions within a single class.
        (Usually, that would be different versions of the extension spec.)
        """
        return [
            a2a.types.AgentExtension(
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
    def from_agent_card(cls, agent: a2a.types.AgentCard) -> typing.Self | None:
        if any(e.uri == cls.URI for e in agent.capabilities.extensions or []):
            return cls()
        return None


ExtensionSpecT = typing.TypeVar("ExtensionSpecT", bound=BaseExtensionSpec)


class BaseExtensionServer(abc.ABC, typing.Generic[ExtensionSpecT, MetadataFromClientT]):
    MetadataFromClient: type[MetadataFromClientT]
    """
    Type of the extension metadata, attached to messages.
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.MetadataFromClient = _get_generic_args(cls, BaseExtensionServer)[1]

    _metadata_from_client: MetadataFromClientT | None = None

    @property
    def data(self):
        return self._metadata_from_client

    def __init__(self, spec: ExtensionSpecT) -> None:
        self.spec = spec

    def parse_client_metadata(self, message: a2a.types.Message) -> MetadataFromClientT | None:
        """
        Server should use this method to retrieve extension-associated metadata from a message.
        """
        return (
            None
            if not message.metadata or self.spec.URI not in message.metadata
            else pydantic.TypeAdapter(self.MetadataFromClient).validate_python(message.metadata[self.spec.URI])
        )

    def handle_incoming_message(self, message: a2a.types.Message, context: Context):
        if self._metadata_from_client is None:
            self._metadata_from_client = self.parse_client_metadata(message)

    def __call__(self, message: a2a.types.Message, context: Context) -> typing.Self:
        self.handle_incoming_message(message, context)
        return self


class BaseExtensionClient(abc.ABC, typing.Generic[ExtensionSpecT, MetadataFromServerT]):
    MetadataFromServer: type[MetadataFromServerT]
    """
    Type of the extension metadata, attached to messages.
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.MetadataFromServer = _get_generic_args(cls, BaseExtensionClient)[1]

    def __init__(self, spec: ExtensionSpecT) -> None:
        self.spec = spec

    def parse_server_metadata(self, message: a2a.types.Message) -> MetadataFromServerT | None:
        """
        Client should use this method to retrieve extension-associated metadata from a message.
        """
        return (
            None
            if not message.metadata or self.spec.URI not in message.metadata
            else pydantic.TypeAdapter(self.MetadataFromServer).validate_python(message.metadata[self.spec.URI])
        )
