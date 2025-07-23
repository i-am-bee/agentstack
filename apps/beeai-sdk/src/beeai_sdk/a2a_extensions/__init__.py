# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

import a2a.types

MetadataT = typing.TypeVar("MetadataT")


class Extension(typing.Protocol, typing.Generic[MetadataT]):
    @classmethod
    def from_agent_card(cls, agent: a2a.types.AgentCard) -> typing.Self | None:
        """
        For the client (user): construct an instance from an agent card.
        """
        ...

    def to_agent_card_extensions(self, *, required: bool) -> list[a2a.types.AgentExtension]:
        """
        For the server (agent): create one or more extension definitions to advertise on the agent card.
        """
        ...

    def parse_message_metadata(self, message: a2a.types.Message) -> MetadataT | None:
        """
        Parse a message and return extension-associated metadata if any.
        """
        ...

    def build_message_metadata(self, *args, **kwargs) -> dict[str, MetadataT]:
        """
        Construct message metadata according to domain specific logic. Return a mergeable metadata dict.
        """
        ...
