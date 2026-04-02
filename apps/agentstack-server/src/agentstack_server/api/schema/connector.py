# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from pydantic import AnyUrl, AwareDatetime, BaseModel, Field, field_validator

from agentstack_server.domain.models.common import Metadata
from agentstack_server.domain.models.connector import ConnectorState


class ConnectorCreateRequest(BaseModel):
    url: AnyUrl

    client_id: str | None = None
    client_secret: str | None = None

    metadata: Metadata | None = None

    match_preset: bool = True


class AuthorizationCodeRequest(BaseModel):
    type: Literal["code"] = "code"
    authorization_endpoint: AnyUrl


AuthorizationRequest = Annotated[AuthorizationCodeRequest, Field(discriminator="type")]


class ConnectorResponse(BaseModel):
    id: UUID
    url: AnyUrl
    state: ConnectorState
    auth_request: AuthorizationRequest | None
    disconnect_reason: str | None
    metadata: Metadata | None
    created_at: AwareDatetime
    updated_at: AwareDatetime
    created_by: UUID


_BLOCKED_HEADERS = frozenset({
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "forwarded",
    "x-forwarded-for",
    "x-forwarded-host",
    "x-forwarded-proto",
    "x-forwarded-port",
    "via",
    "host",
    "cookie",
    "set-cookie",
})


class ConnectorConnectRequest(BaseModel):
    redirect_url: AnyUrl | None = None
    headers: dict[str, str] | None = None

    @field_validator("headers")
    @classmethod
    def validate_headers(cls, v: dict[str, str] | None) -> dict[str, str] | None:
        if v is None:
            return None
        blocked = {k for k in v if k.lower() in _BLOCKED_HEADERS}
        if blocked:
            raise ValueError(f"Blocked header(s): {', '.join(sorted(blocked))}")
        return v


class ConnectorPresetResponse(BaseModel):
    url: AnyUrl
    metadata: Metadata | None
