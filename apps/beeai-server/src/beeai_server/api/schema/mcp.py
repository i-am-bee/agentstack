# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime

from pydantic import BaseModel, field_validator

from beeai_server.domain.models.mcp_provider import (
    McpProviderDeploymentState,
    McpProviderLocation,
    McpProviderTransport,
)


class CreateMcpProviderRequest(BaseModel):
    name: str
    location: McpProviderLocation
    transport: McpProviderTransport


class McpProvider(BaseModel):
    id: str
    name: str
    location: McpProviderLocation
    transport: McpProviderTransport
    state: McpProviderDeploymentState


class ResourceMeta(BaseModel):
    id: str
    uri: str
    name: str
    description: str | None = None
    mime_type: str | None = None
    size: int | None = None

    @field_validator("id", mode="before")
    @classmethod
    def convert_to_str(cls, v):
        return str(v)


class Resource(ResourceMeta):
    text: str | None = None
    blob: bytes | None = None


class Tool(BaseModel):
    id: str
    name: str
    description: str | None = None


class CreateToolkitRequest(BaseModel):
    tools: list[str]


class Toolkit(BaseModel):
    id: str
    location: McpProviderLocation
    transport: McpProviderTransport
    expires_at: datetime
