# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from __future__ import annotations

import types
import typing

import pydantic
import pydantic.config

import beeai_sdk.a2a_extensions


class AgentDetailsTool(pydantic.BaseModel):
    name: str
    description: str


class AgentDetailsLinks(pydantic.BaseModel):
    homepage: str | None = None
    documentation: str | None = None
    source_code: str | None = None
    container_image: str | None = None


class AgentDetailsContributor(pydantic.BaseModel):
    name: str
    email: str | None = None
    url: str | None = None


class AgentDetails(pydantic.BaseModel):
    display_name: str
    ui_type: typing.Literal["chat", "hands-off"] | None = None
    user_greeting: str | None = None
    tools: list[AgentDetailsTool] | None = None
    avg_run_time_seconds: float | None = None
    avg_run_tokens: int | None = None
    framework: str | None = None
    license: str | None = None
    tags: list[str] | None = None
    documentation: str | None = None
    programming_language: str | None = None
    links: AgentDetailsLinks | None = None
    author: AgentDetailsContributor | None = None
    contributors: list[AgentDetailsContributor] | None = None

    model_config: typing.ClassVar[pydantic.config.ConfigDict] = {"extra": "ignore"}


class AgentDetailsExtension(beeai_sdk.a2a_extensions.Extension[AgentDetails, types.NoneType]):
    URI: str = "https://a2a-extensions.beeai.dev/ui/agent_details/v1"
    Params: type[AgentDetails] = AgentDetails
    Metadata: type[types.NoneType] = types.NoneType
