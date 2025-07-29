# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from types import NoneType

import pydantic
from a2a.types import Part

from beeai_sdk.a2a.extensions.base import (
    BaseExtensionClient,
    BaseExtensionServer,
    NoParamsBaseExtensionSpec,
)
from beeai_sdk.a2a.types import AgentMessage


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


class CitationExtensionSpec(NoParamsBaseExtensionSpec):
    URI: str = "https://a2a-extensions.beeai.dev/ui/citation/v1"


class CitationExtensionServer(BaseExtensionServer[CitationExtensionSpec, NoneType]):
    def citation_metadata(
        self,
        *,
        start_index: int | None = None,
        end_index: int | None = None,
        url: str | None = None,
        title: str | None = None,
        description: str | None = None,
    ) -> dict[str, Citation]:
        return {
            self.spec.URI: Citation(
                start_index=start_index,
                end_index=end_index,
                url=url,
                title=title,
                description=description,
            )
        }

    def message(
        self,
        text: str | None = None,
        parts: list[Part] | None = None,
        citation_start_index: int | None = None,
        citation_end_index: int | None = None,
        citation_url: str | None = None,
        citation_title: str | None = None,
        citation_description: str | None = None,
    ) -> AgentMessage:
        return AgentMessage(
            text=text,
            parts=parts or [],
            metadata=self.citation_metadata(
                start_index=citation_start_index,
                end_index=citation_end_index,
                url=citation_url,
                title=citation_title,
                description=citation_description,
            ),
        )


class CitationExtensionClient(BaseExtensionClient[CitationExtensionSpec, Citation]): ...
