# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from a2a.types import AgentExtension
from pydantic import BaseModel

class BeeAIUITool(BaseModel):
    name: str
    description: str

class BeeAIUI(AgentExtension):
    def __init__(self, ui_type: str, user_greeting: str, display_name: str, tools: list[BeeAIUITool]):
        super().__init__(
            uri="beeai_ui",
            params={
                "ui_type": ui_type,
                "user_greeting": user_greeting,
                "display_name": display_name,
                "tools": tools,
            }
        )
