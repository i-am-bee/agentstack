# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from enum import StrEnum

from pydantic import HttpUrl, RootModel

logger = logging.getLogger(__name__)


class McpProviderLocation(RootModel):
    root: HttpUrl


class McpProviderUnmanagedState(StrEnum):
    ONLINE = "online"
    OFFLINE = "offline"


class McpProviderTransport(StrEnum):
    SSE = "sse"
    STREAMABLE_HTTP = "streamable_http"
