# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from contextlib import asynccontextmanager
from types import NoneType
from typing import Annotated, Literal, Self

import a2a.types
import pydantic
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamablehttp_client

from beeai_sdk.a2a.extensions.base import BaseExtensionClient, BaseExtensionServer, BaseExtensionSpec

_TRANSPORT_TYPES = Literal["streamable_http", "stdio"]

_DEFAULT_DEMAND_NAME = "default"
_DEFAULT_ALLOWED_TRANSPORTS: list[_TRANSPORT_TYPES] = ["streamable_http"]


class StdioTransport(pydantic.BaseModel):
    type: Literal["stdio"] = "stdio"

    command: str
    args: list[str]
    env: dict[str, str] | None = None


class StreamableHTTPTransport(pydantic.BaseModel):
    type: Literal["streamable_http"] = "streamable_http"

    url: str


MCPTransport = Annotated[StdioTransport | StreamableHTTPTransport, pydantic.Field(discriminator="type")]


class MCPFulfillment(pydantic.BaseModel):
    transport: MCPTransport


class MCPDemand(pydantic.BaseModel):
    description: str | None = None
    """
    Short description of how the server will be used, what tools should it contain, etc.
    """

    suggested: tuple[str, ...] = ()
    """
    Identifiers of servers recommended to be used. Usually corresponds to MCP StreamableHTTP URIs.
    """

    allowed_transports: list[_TRANSPORT_TYPES] = pydantic.Field(default_factory=lambda: _DEFAULT_ALLOWED_TRANSPORTS)
    """
    Transports allowed for the server. Specifying other transports will result in rejection.
    """


class MCPServiceExtensionParams(pydantic.BaseModel):
    mcp_demands: dict[str, MCPDemand]
    """Server requests that the agent requires to be provided by the client."""


class MCPServiceExtensionSpec(BaseExtensionSpec[MCPServiceExtensionParams]):
    URI: str = "https://a2a-extensions.beeai.dev/services/mcp/v1"

    @classmethod
    def single_demand(
        cls,
        name: str = _DEFAULT_DEMAND_NAME,
        description: str | None = None,
        suggested: tuple[str, ...] = (),
        allowed_transports: list[_TRANSPORT_TYPES] | None = None,
    ) -> Self:
        return cls(
            params=MCPServiceExtensionParams(
                mcp_demands={
                    name: MCPDemand(
                        description=description,
                        suggested=suggested,
                        allowed_transports=allowed_transports or _DEFAULT_ALLOWED_TRANSPORTS,
                    )
                }
            )
        )


class MCPServiceExtensionMetadata(pydantic.BaseModel):
    mcp_fulfillments: dict[str, MCPFulfillment] = {}
    """Provided servers corresponding to the server requests."""


class MCPServiceExtensionServer(BaseExtensionServer[MCPServiceExtensionSpec, MCPServiceExtensionMetadata]):
    def parse_client_metadata(self, message: a2a.types.Message) -> MCPServiceExtensionMetadata | None:
        metadata = super().parse_client_metadata(message)
        if metadata:
            for name, demand in self.spec.params.mcp_demands.items():
                if not (fulfillment := metadata.mcp_fulfillments.get(name)):
                    raise ValueError(f'Fulfillment for demand "{name}" missing')
                if fulfillment.transport.type not in demand.allowed_transports:
                    raise ValueError(f'Transport "{fulfillment.transport.type}" not allowed for demand "{name}"')
        return metadata

    @asynccontextmanager
    async def create_client(self, demand: str = _DEFAULT_DEMAND_NAME):
        fulfillment = self.data.mcp_fulfillments.get(demand) if self.data else None

        if not fulfillment:
            raise ValueError(f'No fulfillment for demand "{demand}"')

        transport = fulfillment.transport

        if isinstance(transport, StdioTransport):
            async with stdio_client(
                server=StdioServerParameters(command=transport.command, args=transport.args, env=transport.env)
            ) as (
                read,
                write,
            ):
                yield (read, write)
        elif isinstance(transport, StreamableHTTPTransport):
            async with streamablehttp_client(url=transport.url) as (read, write, _):
                yield (read, write)
        else:
            raise NotImplementedError("Unsupported transport")


class MCPServiceExtensionClient(BaseExtensionClient[MCPServiceExtensionSpec, NoneType]):
    def fulfillment_metadata(
        self, *, mcp_fulfillments: dict[str, MCPFulfillment]
    ) -> dict[str, MCPServiceExtensionMetadata]:
        return {self.spec.URI: MCPServiceExtensionMetadata(mcp_fulfillments=mcp_fulfillments)}
