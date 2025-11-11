# Copyright 2025 © BeeAI a Series of LF Projects, LLC
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


class Trajectory(pydantic.BaseModel):
    """
    Represents trajectory information for an agent's reasoning or tool execution
    steps. Helps track the agent's decision-making process and provides
    transparency into how the agent arrived at its response.

    Trajectory can capture intermediate steps like:
    - A reasoning step with a message
    - A tool execution with tool name, input, and output

    This information can be used for debugging, audit trails, and providing
    users with insight into the agent's thought process.

    Visually, this may appear as an accordion component in the UI.

    Properties:
    - title: Title of the trajectory update.
    - content: Markdown-formatted content of the trajectory update.
    """

    title: str | None = None
    content: str | None = None
    group_id: str | None = None


class TrajectoryExtensionSpec(NoParamsBaseExtensionSpec):
    URI: str = "https://a2a-extensions.agentstack.beeai.dev/ui/trajectory/v1"


class TrajectoryExtensionServer(BaseExtensionServer[TrajectoryExtensionSpec, NoneType]):
    def trajectory_metadata(
        self, *, title: str | None = None, content: str | None = None, group_id: str | None = None
    ) -> Metadata[str, Any]:
        return Metadata(
            {self.spec.URI: Trajectory(title=title, content=content, group_id=group_id).model_dump(mode="json")}
        )

    def message(
        self,
        text: str | None = None,
        parts: list[Part | TextPart | FilePart | DataPart] | None = None,
        trajectory_title: str | None = None,
        trajectory_content: str | None = None,
    ) -> AgentMessage:
        return AgentMessage(
            text=text,
            parts=parts or [],
            metadata=self.trajectory_metadata(title=trajectory_title, content=trajectory_content),
        )


class TrajectoryExtensionClient(BaseExtensionClient[TrajectoryExtensionSpec, Trajectory]): ...
