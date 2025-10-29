# Copyright 2025 © Agent Stack a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from mcp.client.auth import TokenStorage
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken

from .base import TokenStorageFactory


class MemoryTokenStorage(TokenStorage):
    def __init__(self):
        self.tokens: OAuthToken | None = None
        self.client_info: OAuthClientInformationFull | None = None

    async def get_tokens(self) -> OAuthToken | None:
        return self.tokens

    async def set_tokens(self, tokens: OAuthToken) -> None:
        self.tokens = tokens

    async def get_client_info(self) -> OAuthClientInformationFull | None:
        return self.client_info

    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None:
        self.client_info = client_info


class MemoryTokenStorageFactory(TokenStorageFactory):
    def __init__(self, *, client_info: OAuthClientInformationFull | None = None):
        super().__init__()
        self._client_info = client_info

    async def create_storage(self) -> TokenStorage:
        storage = MemoryTokenStorage()
        if self._client_info:
            await storage.set_client_info(self._client_info)
        return storage
