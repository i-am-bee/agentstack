# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import uuid
from types import NoneType
from typing import TYPE_CHECKING, Self
from urllib.parse import parse_qs

import a2a.types
import pydantic
from mcp.client.auth import OAuthClientProvider
from mcp.shared.auth import OAuthClientMetadata

from beeai_sdk.a2a.extensions.auth.oauth.storage import MemoryTokenStorageFactory, TokenStorageFactory
from beeai_sdk.a2a.extensions.base import BaseExtensionClient, BaseExtensionServer, BaseExtensionSpec
from beeai_sdk.a2a.types import AgentMessage, AuthRequired, RunYieldResume

if TYPE_CHECKING:
    from beeai_sdk.server.context import RunContext

_DEFAULT_DEMAND_NAME = "default"


class AuthRequest(pydantic.BaseModel):
    authorization_endpoint_url: pydantic.AnyUrl


class AuthResponse(pydantic.BaseModel):
    redirect_uri: pydantic.AnyUrl


class OAuthFulfillment(pydantic.BaseModel):
    redirect_uri: pydantic.AnyUrl


class OAuthDemand(pydantic.BaseModel):
    redirect_uri: bool = True


class OAuthExtensionParams(pydantic.BaseModel):
    oauth_demands: dict[str, OAuthDemand]
    """Server requests that the agent requires to be provided by the client."""


class OAuthExtensionSpec(BaseExtensionSpec[OAuthExtensionParams]):
    URI: str = "https://a2a-extensions.beeai.dev/auth/oauth/v1"

    @classmethod
    def single_demand(cls, name: str = _DEFAULT_DEMAND_NAME) -> Self:
        return cls(params=OAuthExtensionParams(oauth_demands={name: OAuthDemand()}))


class OAuthExtensionMetadata(pydantic.BaseModel):
    oauth_fulfillments: dict[str, OAuthFulfillment] = {}
    """Provided servers corresponding to the server requests."""


class OAuthExtensionServer(BaseExtensionServer[OAuthExtensionSpec, OAuthExtensionMetadata]):
    def __init__(self, spec: OAuthExtensionSpec, token_storage_factory: TokenStorageFactory | None = None) -> None:
        super().__init__(spec)
        self.token_storage_factory = token_storage_factory or MemoryTokenStorageFactory()

    def handle_incoming_message(self, message: a2a.types.Message, context: RunContext):
        super().handle_incoming_message(message, context)
        self.context = context

    def _get_fulfillment_for_resource(self, resource_url: pydantic.AnyUrl):
        if not self.data:
            raise RuntimeError("No fulfillments found")

        fulfillment = self.data.oauth_fulfillments.get(str(resource_url)) or self.data.oauth_fulfillments.get(
            _DEFAULT_DEMAND_NAME
        )
        if fulfillment:
            return fulfillment

        raise RuntimeError("Fulfillment not found")

    async def create_httpx_auth(self, *, resource_url: pydantic.AnyUrl):
        fulfillment = self._get_fulfillment_for_resource(resource_url=resource_url)

        resume: RunYieldResume = None

        async def handle_redirect(auth_url: str) -> None:
            nonlocal resume
            if resume:
                raise RuntimeError("Another redirect is already pending")
            message = self.create_auth_request(authorization_endpoint_url=pydantic.AnyUrl(auth_url))
            resume = await self.context.yield_async(AuthRequired(message=message))

        async def handle_callback() -> tuple[str, str | None]:
            nonlocal resume
            try:
                if not resume:
                    raise ValueError("Missing resume data")
                response = self.parse_auth_response(message=resume)
                params = parse_qs(response.redirect_uri.query)
                return params["code"][0], params.get("state", [None])[0]
            finally:
                resume = None

        # A2A Client is responsible for catching the redirect and forwarding it over the A2A connection
        oauth_auth = OAuthClientProvider(
            server_url=str(resource_url),
            client_metadata=OAuthClientMetadata(
                redirect_uris=[fulfillment.redirect_uri],
            ),
            storage=await self.token_storage_factory.create_storage(),
            redirect_handler=handle_redirect,
            callback_handler=handle_callback,
        )
        return oauth_auth

    def create_auth_request(self, *, authorization_endpoint_url: pydantic.AnyUrl):
        data = AuthRequest(authorization_endpoint_url=authorization_endpoint_url)
        return AgentMessage(text="Authorization required", metadata={self.spec.URI: data})

    def parse_auth_response(self, *, message: a2a.types.Message):
        if not message or not message.metadata or not (data := message.metadata.get(self.spec.URI)):
            raise RuntimeError("Invalid auth response")
        return AuthResponse.model_validate(data)


class OAuthExtensionClient(BaseExtensionClient[OAuthExtensionSpec, NoneType]):
    def fulfillment_metadata(
        self, *, oauth_fulfillments: dict[str, OAuthFulfillment]
    ) -> dict[str, OAuthExtensionMetadata]:
        return {self.spec.URI: OAuthExtensionMetadata(oauth_fulfillments=oauth_fulfillments)}

    def parse_auth_request(self, *, message: a2a.types.Message):
        if not message or not message.metadata or not (data := message.metadata.get(self.spec.URI)):
            raise ValueError("Invalid auth request")
        return AuthRequest.model_validate(data)

    def create_auth_response(self, *, task_id: str, redirect_uri: pydantic.AnyUrl):
        data = AuthResponse(redirect_uri=redirect_uri)

        return a2a.types.Message(
            message_id=str(uuid.uuid4()),
            role=a2a.types.Role.user,
            parts=[a2a.types.TextPart(text="Authorization completed")],  # type: ignore
            task_id=task_id,
            metadata={self.spec.URI: data},
        )
