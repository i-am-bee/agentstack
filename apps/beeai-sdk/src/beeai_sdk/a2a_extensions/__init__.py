# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

import a2a.types

ParamsT = typing.TypeVar("ParamsT")
MetadataT = typing.TypeVar("MetadataT")


class Extension(typing.Protocol, typing.Generic[ParamsT, MetadataT]):
    URI: str
    Params: type[ParamsT]
    Metadata: type[MetadataT]

    @classmethod
    def from_agent_card(cls, agent: a2a.types.AgentCard) -> typing.Self | None: ...
    def to_agent_card_extension(self, *, required: bool) -> a2a.types.AgentExtension: ...
    def read_metadata(self, message: a2a.types.Message) -> MetadataT | None: ...
