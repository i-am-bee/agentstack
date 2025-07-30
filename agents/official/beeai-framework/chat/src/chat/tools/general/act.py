# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Literal
from beeai_framework.agents.experimental import (
    RequirementAgent,
    RequirementAgentRunState,
)
from beeai_framework.agents.experimental.events import RequirementAgentStartEvent
from beeai_framework.agents.experimental.requirements import Requirement, Rule
from pydantic import BaseModel, Field, create_model

from beeai_framework.context import RunContext
from beeai_framework.emitter import Emitter, EventMeta
from beeai_framework.tools import (
    JSONToolOutput,
    Tool,
    ToolInputValidationError,
    ToolRunOptions,
)
from beeai_framework.agents.experimental.requirements.requirement import (
    run_with_context,
)


class ActToolInput(BaseModel):
    thought: str = Field(
        ..., description="Precisely describe why do you want to use the tool."
    )
    selected_tool: str = Field(..., description="Select the tool you want to execute.")


class ActToolResult(BaseModel):
    selected_tool: str = Field(
        ..., description="The name of the tool that has been selected for execution."
    )


class ActToolOutput(JSONToolOutput[ActToolResult]):
    pass


class ActTool(Tool[ActToolInput]):
    name: str = "act"
    description: str = "Use whenever you want to use any tool."
    _input_schema: type[BaseModel]

    def __init__(self, *, extra_instructions: str = "") -> None:
        super().__init__()
        self._allowed_tools_names = []
        if extra_instructions:
            self.description += f" {extra_instructions}"

    @property
    def allowed_tools_names(self) -> list[str]:
        """Get the list of allowed tool names."""
        return self._allowed_tools_names

    @allowed_tools_names.setter
    def allowed_tools_names(self, allowed_tools_names: list[str]) -> None:
        """Set the list of allowed tool names."""
        self._allowed_tools_names = allowed_tools_names

        if not allowed_tools_names:
            raise ValueError("Allowed tools names must not be empty.")

        # Hack to create a dynamic input schema based on allowed tools
        self._input_schema = create_model(
            "ActToolInput",
            thought=(
                str,
                Field(
                    ...,
                    description="Precisely describe why do you want to use the tool.",
                ),
            ),
            selected_tool=(
                Literal[tuple(tool_name for tool_name in allowed_tools_names)],
                Field(
                    ...,
                    description=f"Select a tool from the following options: {allowed_tools_names}",
                ),
            ),
        )

    @property
    def input_schema(self):
        return self._input_schema

    async def _run(
        self, input: ActToolInput, options: ToolRunOptions | None, context: RunContext
    ) -> ActToolOutput:
        if not input.selected_tool:
            raise ToolInputValidationError(
                f"You must always select one of the provided tools: {self._allowed_tools_names}."
            )

        if input.selected_tool not in self._allowed_tools_names:
            raise ToolInputValidationError(
                f"Tool '{input.selected_tool}' is not in the list of allowed tools: {self._allowed_tools_names}. Can you please select one of the allowed tools?"
            )

        return ActToolOutput(result=ActToolResult(selected_tool=input.selected_tool))

    def _create_emitter(self) -> Emitter:
        return Emitter.root().child(
            namespace=["tool", "act"],
            creator=self,
        )


class ActAlwaysFirstRequirement(Requirement[RequirementAgentRunState]):
    name: str = "act_always_first"

    @run_with_context
    async def run(self, state: RequirementAgentRunState, ctx: RunContext) -> list[Rule]:
        last_step = state.steps[-1] if state.steps else None
        if last_step and last_step.tool and last_step.tool.name == "act":
            assert isinstance(last_step.tool, ActTool)
            if last_step.error is not None:
                return [
                    Rule(
                        target="act",
                        forced=True,
                        allowed=True,
                        prevent_stop=False,
                        hidden=False,
                    )
                ]

            if last_step.output is None or not isinstance(
                last_step.output, ActToolOutput
            ):
                raise ValueError(
                    "Last step output must be an instance of ActToolOutput."
                )
            selected_tool = last_step.output.result.selected_tool
            return [
                Rule(
                    target=selected_tool,
                    forced=True,
                    allowed=True,
                    prevent_stop=False,
                    hidden=False,
                )
            ]

        return [
            Rule(
                target="act",
                forced=True,
                allowed=True,
                prevent_stop=False,
                hidden=False,
            )
        ]


def act_tool_middleware(ctx: RunContext) -> None:
    assert isinstance(ctx.instance, RequirementAgent)

    act_tool = next((t for t in ctx.instance._tools if isinstance(t, ActTool)), None)
    if act_tool is None:
        raise ValueError("ActTool is not found in the agent's tools.")

    def handle_start(data: RequirementAgentStartEvent, event: EventMeta) -> None:
        allowed_tools = (
            [t.name for t in data.request.tools if t.name != "act"]
            if data.state.iteration == 1
            else [t.name for t in data.request.allowed_tools if t.name != "act"]
        )
        act_tool.allowed_tools_names = allowed_tools

    ctx.emitter.on("start", handle_start)
