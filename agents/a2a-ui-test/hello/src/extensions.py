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
                "avg_run_time_seconds": 24,
                "avg_run_tokens": 5,
                "framework": "BeeAI",
                "license": "GPL v3.0",
                "tags": ["test", "dummy", "hello_world"],
                "programming_language": "python",
                "links": [{"type": "source-code", "url":"https://github.com/i-am-bee/beeai-platform"}],
                "author": { "name": 'Tomas Weiss', "email": "Tomas.Weiss@ibm.com"},
                "contributors": [{ "name": 'Petr Kadlec', "email": "petr.kadlec@ibm.com", "url": "https://research.ibm.com/" },{ "name": "Petr Bulánek", "email": "petr.bulanek@ibm.com" }],
                "documentation": "This is *content* of documentation field in `beeai_ui` agent ~extension~."
            }
        )
