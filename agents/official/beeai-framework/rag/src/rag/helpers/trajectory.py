# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import uuid
from typing import Any, Literal
from beeai_framework.emitter import EventMeta
from beeai_framework.errors import FrameworkError
from beeai_framework.tools import ToolOutput, ToolStartEvent
from beeai_sdk.a2a.extensions.ui.trajectory import TrajectoryExtensionServer
from pydantic import BaseModel, Field, InstanceOf, field_serializer


class TrajectoryEvent(BaseModel):
    kind: str
    parent_id: str | None = None
    phase: Literal["start", "end"] | None
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    def metadata(self, server: TrajectoryExtensionServer):
        return server.trajectory_metadata(
            title=self.kind, content=self.model_dump_json(exclude={"kind"})
        )


class ToolCallTrajectoryEvent(TrajectoryEvent):
    input: Any
    output: InstanceOf[ToolOutput] | None = None
    error: InstanceOf[FrameworkError] | None = None

    @field_serializer("output")
    def serialize_output(self, output: ToolOutput | None) -> Any:
        if output is None:
            return None
        # Check if it's a JSONToolOutput with to_json_safe method
        if hasattr(output, "to_json_safe"):
            return output.to_json_safe()
        # Fallback to text content for other ToolOutput types
        return {"text_content": output.get_text_content()}

    @field_serializer("error")
    def serialize_error(self, error: FrameworkError | None) -> dict[str, Any] | None:
        if error is None:
            return None
        return {"message": str(error), "type": error.__class__.__name__}
