# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from beeai_framework.context import RunContext
from beeai_framework.emitter import Emitter
from beeai_framework.tools import StringToolOutput, Tool, ToolRunOptions
from datetime import datetime

from pydantic import BaseModel


class CurrentTimeToolInput(BaseModel):
    """Input schema for CurrentTimeTool, currently empty as no input is needed."""


class CurrentTimeTool(Tool[CurrentTimeToolInput]):
    name: str = "current_time"
    description: str = (
        "Get current date and time. ALWAYS Use first for questions about recent events or temporal references like 'last', 'today', 'this year'."
    )

    @property
    def input_schema(self) -> type[CurrentTimeToolInput]:
        return CurrentTimeToolInput

    async def _run(
        self,
        input: CurrentTimeToolInput,
        options: ToolRunOptions | None,
        context: RunContext,
    ) -> StringToolOutput:
        current_time_readable = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        return StringToolOutput(current_time_readable)

    def _create_emitter(self) -> Emitter:
        return Emitter.root().child(
            namespace=["tool", "current_time"],
            creator=self,
        )
