# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from types import NoneType
from typing import TYPE_CHECKING

import a2a.types
import pydantic
from pydantic.networks import HttpUrl

from agentstack_sdk.a2a.extensions.base import (
    BaseExtensionClient,
    BaseExtensionServer,
    BaseExtensionSpec,
)
from agentstack_sdk.a2a.extensions.exceptions import ExtensionError
from agentstack_sdk.platform import use_platform_client
from agentstack_sdk.platform.client import PlatformClient

if TYPE_CHECKING:
    from agentstack_sdk.server.context import RunContext


class PlatformApiExtensionMetadata(pydantic.BaseModel):
    base_url: HttpUrl | None = None
    auth_token: pydantic.Secret[str]
    expires_at: pydantic.AwareDatetime | None = None


class PlatformApiExtension(pydantic.BaseModel):
    """
    Request authentication token and url to be able to access the agentstack API
    """


class PlatformApiExtensionParams(pydantic.BaseModel):
    auto_use: bool = True


class PlatformApiExtensionSpec(BaseExtensionSpec[PlatformApiExtensionParams]):
    URI: str = "https://a2a-extensions.agentstack.dev/services/platform_api/v1"

    def __init__(self, params: PlatformApiExtensionParams | None = None) -> None:
        super().__init__(params or PlatformApiExtensionParams())


class PlatformApiExtensionServer(BaseExtensionServer[PlatformApiExtensionSpec, PlatformApiExtensionMetadata]):
    context_id: str | None = None

    def parse_client_metadata(self, message: a2a.types.Message) -> PlatformApiExtensionMetadata | None:
        self.context_id = message.context_id
        # we assume that the context id is the same ID as the platform context id
        # if different IDs are passed, api requests to platform using this token will fail
        return super().parse_client_metadata(message)

    @asynccontextmanager
    async def lifespan(self) -> AsyncIterator[None]:
        """Called when entering the agent context after the first message was parsed (__call__ was already called)"""
        if self.data and self.spec.params.auto_use:
            async with self.use_client():
                yield
        else:
            yield

    def handle_incoming_message(self, message: a2a.types.Message, context: RunContext):
        super().handle_incoming_message(message, context)
        if self.data:
            self.data.base_url = self.data.base_url or HttpUrl(os.getenv("PLATFORM_URL", "http://127.0.0.1:8333"))

    @asynccontextmanager
    async def use_client(self) -> AsyncIterator[PlatformClient]:
        if not self.data:
            raise ExtensionError(self.spec, "Platform extension metadata was not provided")
        auth_token = self.data.auth_token.get_secret_value()
        async with use_platform_client(
            context_id=self.context_id,
            base_url=str(self.data.base_url),
            auth_token=auth_token,
        ) as client:
            yield client


class PlatformApiExtensionClient(BaseExtensionClient[PlatformApiExtensionSpec, NoneType]):
    def api_auth_metadata(
        self,
        *,
        auth_token: pydantic.Secret[str] | str,
        expires_at: pydantic.AwareDatetime | None = None,
        base_url: HttpUrl | None = None,
    ) -> dict[str, dict[str, str]]:
        return {
            self.spec.URI: {
                **PlatformApiExtensionMetadata(
                    base_url=base_url,
                    auth_token=pydantic.Secret("replaced below"),
                    expires_at=expires_at,
                ).model_dump(mode="json"),
                "auth_token": auth_token if isinstance(auth_token, str) else auth_token.get_secret_value(),
            }
        }


class _PlatformSelfRegistrationExtension(pydantic.BaseModel):
    """Internal extension"""


class _PlatformSelfRegistrationExtensionParams(pydantic.BaseModel):
    self_registration_id: str


class _PlatformSelfRegistrationExtensionSpec(BaseExtensionSpec[_PlatformSelfRegistrationExtensionParams]):
    URI: str = "https://a2a-extensions.agentstack.dev/services/platform-self-registration/v1"
