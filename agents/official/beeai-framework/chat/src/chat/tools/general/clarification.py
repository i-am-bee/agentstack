# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from beeai_framework.agents.experimental import (
    RequirementAgent,
    RequirementAgentRunState,
)
from beeai_framework.agents.experimental.events import RequirementAgentStartEvent
from beeai_framework.backend import AssistantMessage
from pydantic import BaseModel, Field
from beeai_framework.tools import (
    Tool,
    ToolInputValidationError,
    ToolRunOptions,
    StringToolOutput,
)
from beeai_framework.context import RunContext
from beeai_framework.emitter import Emitter, EventMeta


class ClarificationSchema(BaseModel):
    thoughts: str = Field(..., description="Thoughts about the question.")
    question_to_user: str = Field(
        ..., description="Question to the user.", min_length=1
    )


class ClarificationTool(Tool[ClarificationSchema]):
    name: str = "clarification"
    description: str = "Use when you need to clarify something from user."

    @property
    def state(self) -> RequirementAgentRunState:
        """Get the state of the tool."""
        return self._state

    @state.setter
    def state(self, state: RequirementAgentRunState) -> None:
        """Set the state of the tool."""
        self._state = state

    @property
    def input_schema(self) -> type[ClarificationSchema]:
        return ClarificationSchema

    async def _run(
        self,
        input: ClarificationSchema,
        options: ToolRunOptions | None,
        context: RunContext,
    ) -> StringToolOutput:
        if not self._state:
            raise ToolInputValidationError(
                "State is not set for the ClarificationTool."
            )

        self._state.result = input
        self._state.answer = AssistantMessage(input.question_to_user)  # type: ignore

        return StringToolOutput("Question has been sent")

    def _create_emitter(self) -> Emitter:
        return Emitter.root().child(
            namespace=["tool", "clarification"],
            creator=self,
        )


def clarification_tool_middleware(ctx: RunContext) -> None:
    assert isinstance(ctx.instance, RequirementAgent)

    clarification_tool = next(
        (t for t in ctx.instance._tools if isinstance(t, ClarificationTool)), None
    )
    if clarification_tool is None:
        raise ValueError("ClarificationTool is not found in the agent's tools.")

    def handle_start(data: RequirementAgentStartEvent, event: EventMeta) -> None:
        clarification_tool.state = data.state

    ctx.emitter.on("start", handle_start)
