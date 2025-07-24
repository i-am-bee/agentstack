# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import abc
import typing

import a2a.types
import pydantic

ParamsT = typing.TypeVar("ParamsT")
MetadataT = typing.TypeVar("MetadataT")


class Extension(abc.ABC, typing.Generic[ParamsT, MetadataT]):
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

    Metadata: type[MetadataT]
    """
    Type of the extension metadata, attached to messages.
    """

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
                    dict[str, typing.Any], pydantic.TypeAdapter(self.Params).dump_python(self.params, mode="json")
                ),
                required=required,
            )
        ]

    def parse_message_metadata(self, message: a2a.types.Message) -> MetadataT | None:
        """
        Client should use this method to retrieve extension-associated metadata from a message.
        """
        return (
            None
            if not message.metadata or self.URI not in message.metadata
            else pydantic.TypeAdapter(self.Metadata).validate_python(message.metadata[self.URI])
        )
