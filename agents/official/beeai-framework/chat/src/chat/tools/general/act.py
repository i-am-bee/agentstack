# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Literal

from beeai_framework.agents.experimental import (
    RequirementAgent,
    RequirementAgentRunState,
)
from beeai_framework.agents.experimental.events import RequirementAgentStartEvent
from beeai_framework.agents.experimental.requirements import Requirement, Rule
from beeai_framework.agents.experimental.requirements.requirement import (
    run_with_context,
)
from beeai_framework.context import RunContext
from beeai_framework.emitter import Emitter, EventMeta
from beeai_framework.tools import (
    JSONToolOutput,
    Tool,
    ToolInputValidationError,
    ToolRunOptions,
)
from pydantic import BaseModel, Field, create_model


class ActToolInput(BaseModel):
    thought: str = Field(
        ...,
        description="Provide a clear explanation of why you want to use the selected tool and what you expect to achieve.",
    )
    selected_tool: str = Field(
        ..., description="The name of the tool you want to execute next."
    )


class ActToolResult(BaseModel):
    selected_tool: str = Field(
        ..., description="The name of the tool that has been selected for execution."
    )


class ActToolOutput(JSONToolOutput[ActToolResult]):
    pass


class ActTool(Tool[ActToolInput]):
    """
    An auxiliary tool that ensures correct thinking sequence by forcing deliberate tool selection.

    This tool must be used in tandem with ActAlwaysFirstRequirement. It enforces that the LLM
    must first think about and explicitly select which tool to use before executing any other tool.
    The selected_tool from the output is then enforced to run next.

    This pattern promotes more thoughtful and deliberate tool usage by requiring the agent to
    explicitly state its reasoning and tool choice before execution.
    """

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
                    description="Provide a clear explanation of why you want to use the selected tool and what you expect to achieve.",
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
    """
    A requirement that enforces the ActTool to be used before any other tool execution.

    This requirement ensures that:
    1. On the first step, only the ActTool can be executed
    2. After ActTool execution, only the tool selected by ActTool can be executed
    3. If ActTool encounters an error, it must be used again

    This creates a controlled execution flow where every tool usage must be preceded
    by explicit tool selection through the ActTool, promoting more deliberate and
    thoughtful agent behavior.
    """

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
    """
    Middleware function that configures the ActTool with allowed tools at runtime.
    """
    assert isinstance(ctx.instance, RequirementAgent)

    act_tool = next((t for t in ctx.instance._tools if isinstance(t, ActTool)), None)
    if act_tool is None:
        raise ValueError("ActTool is not found in the agent's tools.")

    def handle_start(data: RequirementAgentStartEvent, event: EventMeta) -> None:
        allowed_tools = [t.name for t in data.request.tools if t.name != "act"]
        act_tool.allowed_tools_names = allowed_tools

    ctx.emitter.on("start", handle_start)
