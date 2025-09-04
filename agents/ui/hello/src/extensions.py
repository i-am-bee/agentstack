# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from a2a.types import AgentExtension
from pydantic import BaseModel


class BeeAIUITool(BaseModel):
    name: str
    description: str


class AgentDetailContributor(BaseModel):
    name: str
    email: str | None = None
    url: str | None = None


class BeeAIUI(AgentExtension):
    def __init__(
        self,
        interaction_mode: str,
        user_greeting: str,
        tools: list[BeeAIUITool],
        framework: str,
        license: str,
        programming_language: str,
        source_code_url: str,
        container_image_url: str | None = None,
        author: AgentDetailContributor | None = None,
        contributors: list[AgentDetailContributor] | None = None,
    ):
        super().__init__(
            uri="https://a2a-extensions.beeai.dev/ui/agent-detail/v1",
            params={
                "interaction_mode": interaction_mode,
                "user_greeting": user_greeting,
                "tools": tools,
                "framework": framework,
                "license": license,
                "programming_language": programming_language,
                "source_code_url": source_code_url,
                "container_image_url": container_image_url,
                "author": author,
                "contributors": contributors,
            },
        )
