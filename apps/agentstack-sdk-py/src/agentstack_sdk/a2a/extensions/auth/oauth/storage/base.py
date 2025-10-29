# Copyright 2025 © Agent Stack a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import abc

from mcp.client.auth import TokenStorage


class TokenStorageFactory(abc.ABC):
    @abc.abstractmethod
    async def create_storage(self) -> TokenStorage: ...
