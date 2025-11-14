# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from datetime import timedelta
from typing import Any, Self

from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from mcp import ClientSession
from mcp.client.session import ElicitationFnT, ListRootsFnT, LoggingFnT, MessageHandlerFnT, SamplingFnT
from mcp.shared.message import SessionMessage
from mcp.shared.session import ProgressFnT
from mcp.types import CallToolResult, Implementation

from agentstack_sdk.a2a.extensions.mcp import MCPExtensionServer, ToolCallApprovalRequest
from agentstack_sdk.server.context import RunContext


class MCPClientSession(ClientSession):
    def __init__(
        self,
        read_stream: MemoryObjectReceiveStream[SessionMessage | Exception],
        write_stream: MemoryObjectSendStream[SessionMessage],
        read_timeout_seconds: timedelta | None = None,
        sampling_callback: SamplingFnT | None = None,
        elicitation_callback: ElicitationFnT | None = None,
        list_roots_callback: ListRootsFnT | None = None,
        logging_callback: LoggingFnT | None = None,
        message_handler: MessageHandlerFnT | None = None,
        client_info: Implementation | None = None,
        *,
        context: RunContext,
    ) -> None:
        super().__init__(
            read_stream,
            write_stream,
            read_timeout_seconds,
            sampling_callback,
            elicitation_callback,
            list_roots_callback,
            logging_callback,
            message_handler,
            client_info,
        )
        self._context = context
        self._mcp_extension = None

    def apply(self, extension: MCPExtensionServer) -> Self:
        self._mcp_extension = extension
        return self

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
        read_timeout_seconds: timedelta | None = None,
        progress_callback: ProgressFnT | None = None,
    ) -> CallToolResult:
        """Send a tools/call request with optional progress callback support."""

        if self._mcp_extension:
            await self._mcp_extension.raise_tool_approval(
                request=ToolCallApprovalRequest(name=name, arguments=arguments), context=self._context
            )

        return await super().call_tool(name, arguments, read_timeout_seconds, progress_callback)
