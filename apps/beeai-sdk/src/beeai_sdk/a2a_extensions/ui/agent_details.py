# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from __future__ import annotations

import types
import typing

import pydantic
import pydantic.config

from beeai_sdk.a2a_extensions.base_extension import BaseExtension


class AgentDetailsTool(pydantic.BaseModel):
    name: str
    description: str


class AgentDetailsContributor(pydantic.BaseModel):
    name: str
    email: str | None = None
    url: str | None = None


class AgentDetails(pydantic.BaseModel):
    ui_type: str | None = pydantic.Field(examples=["chat", "hands-off"])
    user_greeting: str | None = None
    tools: list[AgentDetailsTool] | None = None
    framework: str | None = None
    license: str | None = None
    programming_language: str | None = None
    homepage_url: str | None = None
    source_code_url: str | None = None
    container_image_url: str | None = None
    author: AgentDetailsContributor | None = None
    contributors: list[AgentDetailsContributor] | None = None

    model_config: typing.ClassVar[pydantic.config.ConfigDict] = {"extra": "ignore"}


class AgentDetailsExtension(BaseExtension[AgentDetails, types.NoneType]):
    URI: str = "https://a2a-extensions.beeai.dev/ui/agent_details/v1"
    Params: type[AgentDetails] = AgentDetails
    Metadata: type[types.NoneType] = types.NoneType
