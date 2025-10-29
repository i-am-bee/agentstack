# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

import pydantic
from a2a.types import Artifact
from a2a.types import Message as A2AMessage

if TYPE_CHECKING:
    from agentstack_sdk.server.context import RunContext

from agentstack_sdk.a2a.extensions.base import (
    BaseExtensionServer,
    NoParamsBaseExtensionSpec,
)


class CanvasEditRequestMetadata(pydantic.BaseModel):
    start_index: int
    end_index: int
    description: str
    artifact_id: str


class CanvasEditRequest(pydantic.BaseModel):
    start_index: int
    end_index: int
    description: str
    artifact: Artifact


class CanvasExtensionSpec(NoParamsBaseExtensionSpec):
    URI: str = "https://a2a-extensions.agentstack.dev/ui/canvas/v1"


class CanvasExtensionServer(BaseExtensionServer[CanvasExtensionSpec, CanvasEditRequestMetadata]):
    def handle_incoming_message(self, message: A2AMessage, context: RunContext):
        super().handle_incoming_message(message, context)
        self.context = context

    async def parse_canvas_edit_request(self, *, message: A2AMessage) -> CanvasEditRequest | None:
        if not message or not message.metadata or not (data := message.metadata.get(self.spec.URI)):
            return None

        metadata = CanvasEditRequestMetadata.model_validate(data)

        try:
            artifact = await anext(
                artifact
                async for artifact in self.context.load_history()
                if isinstance(artifact, Artifact) and artifact.parts
                if artifact.artifact_id == metadata.artifact_id
            )
        except StopAsyncIteration as e:
            raise ValueError(f"Artifact {metadata.artifact_id} not found in history") from e

        return CanvasEditRequest(
            start_index=metadata.start_index,
            end_index=metadata.end_index,
            description=metadata.description,
            artifact=artifact,
        )
