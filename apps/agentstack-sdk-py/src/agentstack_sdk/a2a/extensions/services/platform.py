# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from types import NoneType
from typing import TYPE_CHECKING

import pydantic
from a2a.server.agent_execution.context import RequestContext
from a2a.types import Message as A2AMessage
from fastapi.security.utils import get_authorization_scheme_param
from pydantic.networks import HttpUrl
from typing_extensions import override

from agentstack_sdk.a2a.extensions.base import (
    BaseExtensionClient,
    BaseExtensionServer,
    BaseExtensionSpec,
)
from agentstack_sdk.a2a.extensions.exceptions import ExtensionError
from agentstack_sdk.platform import use_platform_client
from agentstack_sdk.platform.client import PlatformClient
from agentstack_sdk.server.middleware.platform_auth_backend import PlatformAuthenticatedUser
from agentstack_sdk.util.httpx import BearerAuth

if TYPE_CHECKING:
    from agentstack_sdk.server.context import RunContext


class PlatformApiExtensionMetadata(pydantic.BaseModel):
    base_url: HttpUrl | None = None
    auth_token: pydantic.Secret[str] | None = None
    expires_at: pydantic.AwareDatetime | None = None


class PlatformApiExtension(pydantic.BaseModel):
    """
    Request authentication token and url to be able to access the agentstack API
    """


class PlatformApiExtensionParams(pydantic.BaseModel):
    auto_use: bool = True


class PlatformApiExtensionSpec(BaseExtensionSpec[PlatformApiExtensionParams]):
    URI: str = "https://a2a-extensions.agentstack.beeai.dev/services/platform_api/v1"

    def __init__(self, params: PlatformApiExtensionParams | None = None) -> None:
        super().__init__(params or PlatformApiExtensionParams())


class PlatformApiExtensionServer(BaseExtensionServer[PlatformApiExtensionSpec, PlatformApiExtensionMetadata]):
    context_id: str | None = None

    @asynccontextmanager
    @override
    async def lifespan(self) -> AsyncIterator[None]:
        """Called when entering the agent context after the first message was parsed (__call__ was already called)"""
        if self.data and self.spec.params.auto_use:
            async with self.use_client():
                yield
        else:
            yield

    def _get_header_token(self, request_context: RequestContext) -> pydantic.Secret[str] | None:
        header_token = None
        call_context = request_context.call_context
        assert call_context
        if isinstance(call_context.user, PlatformAuthenticatedUser):
            header_token = call_context.user.auth_token.get_secret_value()
        elif auth_header := call_context.state.get("headers", {}).get("authorization", None):
            _scheme, header_token = get_authorization_scheme_param(auth_header)
        return pydantic.Secret(header_token) if header_token else None

    @override
    def handle_incoming_message(self, message: A2AMessage, run_context: RunContext, request_context: RequestContext):
        super().handle_incoming_message(message, run_context, request_context)
        # we assume that request context id is the same ID as the platform context id
        # if different IDs are passed, api requests to platform using this token will fail
        self.context_id = request_context.context_id

        self._metadata_from_client = self._metadata_from_client or PlatformApiExtensionMetadata()
        data = self._metadata_from_client
        data.base_url = data.base_url or HttpUrl(os.getenv("PLATFORM_URL", "http://127.0.0.1:8333"))
        data.auth_token = data.auth_token or self._get_header_token(request_context)

        if not data.auth_token:
            raise ExtensionError(self.spec, "Platform extension metadata was not provided")

    @asynccontextmanager
    async def use_client(self) -> AsyncIterator[PlatformClient]:
        if not self.data or not self.data.auth_token:
            raise ExtensionError(self.spec, "Platform extension metadata was not provided")
        async with use_platform_client(
            context_id=self.context_id,
            base_url=str(self.data.base_url),
            auth_token=self.data.auth_token.get_secret_value(),
        ) as client:
            yield client

    async def create_httpx_auth(self) -> BearerAuth:
        if not self.data or not self.data.auth_token:
            raise ExtensionError(self.spec, "Platform extension metadata was not provided")
        return BearerAuth(token=self.data.auth_token.get_secret_value())


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
    URI: str = "https://a2a-extensions.agentstack.beeai.dev/services/platform-self-registration/v1"
