# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pydantic

from beeai_sdk.a2a_extensions.base_extension import BaseExtension


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


class TrajectoryExtension(BaseExtension[pydantic.BaseModel, Trajectory]):
    URI: str = "https://a2a-extensions.beeai.dev/ui/trajectory/v1"
    Params: type[pydantic.BaseModel] = pydantic.BaseModel
    Metadata: type[Trajectory] = Trajectory

    def trajectory_metadata(
        self,
        *,
        title: str | None = None,
        content: str | None = None,
    ) -> dict[str, Trajectory]:
        return {
            self.URI: Trajectory(
                title=title,
                content=content,
            )
        }
