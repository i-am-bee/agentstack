# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID, uuid4

from pydantic import AnyUrl, AwareDatetime, BaseModel, BeforeValidator, ConfigDict, Field

from agentstack_server.domain.models.common import Metadata
from agentstack_server.utils.utils import utc_now


class AuthorizationCodeFlow(BaseModel):
    type: Literal["code"] = "code"
    authorization_endpoint: AnyUrl
    state: str
    code_verifier: str
    redirect_uri: str
    client_redirect_uri: AnyUrl | None


AuthFlow = Annotated[AuthorizationCodeFlow, Field(discriminator="type")]


def normalize_bearer(v: object) -> str:
    if not isinstance(v, str):
        raise ValueError("token_type must be a string")
    v_lower = v.lower()
    if v_lower != "bearer":
        raise ValueError(f"token_type must be 'bearer', got '{v}'")
    return v_lower


class Token(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: Annotated[Literal["bearer"], BeforeValidator(normalize_bearer)]

    model_config = ConfigDict(extra="allow")


class Authorization(BaseModel):
    client_id: str | None = None
    client_secret: str | None = None
    flow: AuthFlow | None = None
    token: Token | None = None
    token_endpoint: AnyUrl | None = None


class ConnectorState(StrEnum):
    created = "created"
    auth_required = "auth_required"
    connected = "connected"
    disconnected = "disconnected"


class Connector(BaseModel):
    id: UUID = Field(default_factory=uuid4)

    url: AnyUrl

    state: ConnectorState = ConnectorState.created

    auth: Authorization | None = None
    disconnect_reason: str | None = None

    created_at: AwareDatetime = Field(default_factory=utc_now)
    updated_at: AwareDatetime = Field(default_factory=utc_now)
    created_by: UUID

    metadata: Metadata | None = None
