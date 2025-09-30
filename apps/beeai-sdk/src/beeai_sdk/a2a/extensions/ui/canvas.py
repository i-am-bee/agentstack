# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

import pydantic
from a2a.types import Artifact
from a2a.types import Message as A2AMessage

if TYPE_CHECKING:
    from beeai_sdk.server.context import RunContext

from beeai_sdk.a2a.extensions.base import (
    BaseExtensionServer,
    NoParamsBaseExtensionSpec,
)


class ArtifactChange(pydantic.BaseModel):
    start_index: int
    end_index: int
    artifact_id: str


class ArtifactChangeResponse(ArtifactChange):
    artifact: Artifact


class CanvasExtensionSpec(NoParamsBaseExtensionSpec):
    URI: str = "https://a2a-extensions.beeai.dev/ui/canvas/v1"


class CanvasExtensionServer(BaseExtensionServer[CanvasExtensionSpec, ArtifactChange]):
    def handle_incoming_message(self, message: A2AMessage, context: RunContext):
        super().handle_incoming_message(message, context)
        self.context = context

    async def parse_canvas_response(self, *, message: A2AMessage) -> ArtifactChange | None:
        if not message or not message.metadata or not (data := message.metadata.get(self.spec.URI)):
            return None

        artifact_change = ArtifactChange.model_validate(data)
        self.context.store.load_history()

        history = [
            message
            async for message in self.context.store.load_history()
            if isinstance(message, Artifact) and message.parts
        ]
        for message in history:
            if message.artifact_id == artifact_change.artifact_id:
                return ArtifactChangeResponse(
                    start_index=artifact_change.start_index,
                    end_index=artifact_change.end_index,
                    artifact_id=message.artifact_id,
                    artifact=message,
                )

        raise ValueError(f"Artifact {artifact_change.artifact_id} not found in history")
