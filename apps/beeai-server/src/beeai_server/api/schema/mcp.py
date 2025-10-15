# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime

from pydantic import BaseModel

from beeai_server.domain.models.mcp_provider import (
    McpProviderLocation,
    McpProviderTransport,
    McpProviderUnmanagedState,
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
    state: McpProviderUnmanagedState


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
