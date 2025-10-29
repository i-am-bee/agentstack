# Copyright 2025 © Agent Stack a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from types import NoneType
from typing import Any

import pydantic
from a2a.types import DataPart, FilePart, Part, TextPart

from agentstack_sdk.a2a.extensions.base import (
    BaseExtensionClient,
    BaseExtensionServer,
    NoParamsBaseExtensionSpec,
)
from agentstack_sdk.a2a.types import AgentMessage, Metadata


class Citation(pydantic.BaseModel):
    """
    Represents an inline citation, providing info about information source. This
    is supposed to be rendered as an inline icon, optionally marking a text
    range it belongs to.

    If Citation is included together with content in the message part,
    the citation belongs to that content and renders at the Part position.
    This way may be used for non-text content, like images and files.

    Alternatively, `start_index` and `end_index` may define a text range,
    counting characters in the current Message across all Parts containing plain
    text, where the citation will be rendered. If one of `start_index` and
    `end_index` is missing or their values are equal, the citation renders only
    as an inline icon at that position.

    If both `start_index` and `end_index` are not present and Part has empty
    content, the citation renders as inline icon only at the Part position.

    Properties:
    - url: URL of the source document.
    - title: Title of the source document.
    - description: Accompanying text, which may be a general description of the
                   source document, or a specific snippet.
    """

    start_index: int | None = None
    end_index: int | None = None
    url: str | None = None
    title: str | None = None
    description: str | None = None


class CitationMetadata(pydantic.BaseModel):
    citations: list[Citation] = pydantic.Field(default_factory=list)


class CitationExtensionSpec(NoParamsBaseExtensionSpec):
    URI: str = "https://a2a-extensions.agentstack.dev/ui/citation/v1"


class CitationExtensionServer(BaseExtensionServer[CitationExtensionSpec, NoneType]):
    def citation_metadata(
        self,
        *,
        citations: list[Citation],
    ) -> Metadata[str, Any]:
        return Metadata({self.spec.URI: CitationMetadata(citations=citations).model_dump(mode="json")})

    def message(
        self,
        text: str | None = None,
        parts: list[Part | TextPart | FilePart | DataPart] | None = None,
        *,
        citations: list[Citation],
    ) -> AgentMessage:
        return AgentMessage(
            text=text,
            parts=parts or [],
            metadata=self.citation_metadata(citations=citations),
        )


class CitationExtensionClient(BaseExtensionClient[CitationExtensionSpec, CitationMetadata]): ...
