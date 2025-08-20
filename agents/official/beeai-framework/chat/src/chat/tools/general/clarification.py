# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from beeai_framework.agents.experimental import (
    RequirementAgent,
    RequirementAgentRunState,
)
from beeai_framework.agents.experimental.events import RequirementAgentStartEvent
from beeai_framework.backend import AssistantMessage
from beeai_framework.context import RunContext
from beeai_framework.emitter import Emitter, EventMeta
from beeai_framework.tools import (
    StringToolOutput,
    Tool,
    ToolInputValidationError,
    ToolRunOptions,
)
from pydantic import BaseModel, Field


class ClarificationSchema(BaseModel):
    thoughts: str = Field(
        ..., description="Your reasoning process and analysis of what information is needed from the user."
    )
    question_to_user: str = Field(
        ..., description="The specific question or clarification request to ask the user.", min_length=1
    )


class ClarificationTool(Tool[ClarificationSchema]):
    """
    An auxiliary tool that enables agents to ask clarifying questions when user requirements are unclear.

    This tool prevents agents from making assumptions or providing incomplete answers by allowing them
    to request additional information from the user. It's particularly useful for smaller models that
    might otherwise attempt to complete tasks with insufficient information.

    The tool captures the agent's reasoning process and formulates appropriate questions to ensure
    better task understanding and more accurate results.
    """

    name: str = "clarification"
    description: str = "Use when you need to clarify something from user."

    @property
    def state(self) -> RequirementAgentRunState:
        """Get the current agent state that this tool will use for question handling."""
        return self._state

    @state.setter
    def state(self, state: RequirementAgentRunState) -> None:
        """Set the agent state that this tool will use for question handling."""
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
            raise ToolInputValidationError("State is not set for the ClarificationTool.")

        # Store the clarification request in the agent state
        self._state.result = input
        # Set the question as the agent's response to the user
        self._state.answer = AssistantMessage(input.question_to_user)  # type: ignore

        return StringToolOutput("Question has been sent")

    def _create_emitter(self) -> Emitter:
        return Emitter.root().child(namespace=["tool", "clarification"], creator=self)


def clarification_tool_middleware(ctx: RunContext) -> None:
    """
    Middleware function that provides the ClarificationTool with access to the agent's state.

    This middleware enables the ClarificationTool to bypass the normal final answer flow by directly
    setting the agent's answer when asking clarifying questions.
    """
    assert isinstance(ctx.instance, RequirementAgent)

    clarification_tool = next((t for t in ctx.instance._tools if isinstance(t, ClarificationTool)), None)
    if clarification_tool is None:
        raise ValueError("ClarificationTool is not found in the agent's tools.")

    def handle_start(data: RequirementAgentStartEvent, event: EventMeta) -> None:
        clarification_tool.state = data.state

    ctx.emitter.on("start", handle_start)
