# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from __future__ import annotations

import typing
from types import NoneType

import pydantic
import pydantic.config

from beeai_sdk.a2a.extensions.base import BaseExtensionClient, BaseExtensionServer, BaseExtensionSpec


class AgentDetailTool(pydantic.BaseModel):
    name: str
    description: str


class AgentDetailContributor(pydantic.BaseModel):
    name: str
    email: str | None = None
    url: str | None = None


class AgentDetail(pydantic.BaseModel):
    ui_type: str | None = pydantic.Field("chat", examples=["chat", "hands-off"])
    user_greeting: str | None = None
    tools: list[AgentDetailTool] | None = None
    framework: str | None = None
    license: str | None = None
    programming_language: str | None = None
    homepage_url: str | None = None
    source_code_url: str | None = None
    container_image_url: str | None = None
    author: AgentDetailContributor | None = None
    contributors: list[AgentDetailContributor] | None = None

    model_config: typing.ClassVar[pydantic.config.ConfigDict] = {"extra": "ignore"}


class AgentDetailExtensionSpec(BaseExtensionSpec[AgentDetail]):
    URI: str = "https://a2a-extensions.beeai.dev/ui/agent-detail/v1"


class AgentDetailExtensionServer(BaseExtensionServer[AgentDetailExtensionSpec, NoneType]): ...


class AgentDetailExtensionClient(BaseExtensionClient[AgentDetailExtensionSpec, AgentDetail]): ...
