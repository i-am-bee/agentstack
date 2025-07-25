# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pydantic

from beeai_sdk.a2a_extensions.base_extension import BaseExtension


class Trajectory(pydantic.BaseModel):
    """
    Represents trajectory information for an agent's reasoning or tool execution
    steps. This metadata helps track the agent's decision-making process and
    provides transparency into how the agent arrived at its response.

    TrajectoryMetadata can capture either:
    1. A reasoning step with a message
    2. A tool execution with tool name, input, and output

    This information can be used for debugging, audit trails, and providing
    users with insight into the agent's thought process.

    Properties:
    - message: A reasoning step or thought in the agent's decision process.
    - tool_name: Name of the tool that was executed.
    - tool_input: Input parameters passed to the tool.
    - tool_output: Output or result returned by the tool.
    """

    message: str | None = None
    tool_name: str | None = None
    tool_input: str | None = None
    tool_output: str | None = None


class TrajectoryExtension(BaseExtension[pydantic.BaseModel, Trajectory]):
    URI: str = "https://a2a-extensions.beeai.dev/ui/trajectory/v1"
    Params: type[pydantic.BaseModel] = pydantic.BaseModel
    Metadata: type[Trajectory] = Trajectory

    def trajectory_metadata(
        self,
        *,
        message: str | None = None,
        tool_name: str | None = None,
        tool_input: str | None = None,
        tool_output: str | None = None,
    ) -> dict[str, Trajectory]:
        return {
            self.URI: Trajectory(
                message=message,
                tool_name=tool_name,
                tool_input=tool_input,
                tool_output=tool_output,
            )
        }
