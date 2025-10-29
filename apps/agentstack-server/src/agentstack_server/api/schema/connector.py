# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated, Literal
from uuid import UUID

from pydantic import AnyUrl, BaseModel, Field

from agentstack_server.domain.models.common import Metadata
from agentstack_server.domain.models.connector import ConnectorState


class ConnectorCreateRequest(BaseModel):
    url: AnyUrl

    client_id: str | None = None
    client_secret: str | None = None

    metadata: Metadata | None = None


class AuthorizationCodeRequest(BaseModel):
    type: Literal["code"] = "code"
    authorization_endpoint: AnyUrl


AuthorizationRequest = Annotated[AuthorizationCodeRequest, Field(discriminator="type")]


class ConnectorResponse(BaseModel):
    id: UUID
    url: AnyUrl
    state: ConnectorState
    auth_request: AuthorizationRequest | None = None
    disconnect_reason: str | None = None
    metadata: Metadata | None = None


class ConnectorConnectRequest(BaseModel):
    redirect_url: AnyUrl | None = None
