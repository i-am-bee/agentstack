# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

# This should really be imported from the SDK
# However, that is technically challenging with the current workspaces and build setup

from __future__ import annotations

from typing import Annotated, Literal

import pydantic


class StdioTransport(pydantic.BaseModel):
    type: Literal["stdio"] = "stdio"

    command: str
    args: list[str]
    env: dict[str, str] | None = None


class StreamableHTTPTransport(pydantic.BaseModel):
    type: Literal["streamable_http"] = "streamable_http"

    url: pydantic.AnyHttpUrl
    headers: dict[str, str] | None = None


MCPTransport = Annotated[StdioTransport | StreamableHTTPTransport, pydantic.Field(discriminator="type")]


class MCPFulfillment(pydantic.BaseModel):
    transport: MCPTransport


MCPServiceExtensionURI = "https://a2a-extensions.agentstack.beeai.dev/services/mcp/v1"


class MCPServiceExtensionMetadata(pydantic.BaseModel):
    mcp_fulfillments: dict[str, MCPFulfillment] = {}
    """Provided servers corresponding to the server requests."""
