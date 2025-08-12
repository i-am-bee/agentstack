# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from datetime import timedelta
from typing import Any
from uuid import UUID

import jwt
from pydantic import AwareDatetime, BaseModel

from beeai_server.configuration import Configuration
from beeai_server.domain.models.permissions import Permissions
from beeai_server.domain.models.user import UserRole
from beeai_server.utils.utils import utc_now

ROLE_PERMISSIONS: dict[UserRole, Permissions] = {
    UserRole.admin: Permissions.all(),
    UserRole.user: Permissions(
        files={"*"},
        vector_stores={"*"},
        llm={"*"},
        embeddings={"*"},
        a2a_proxy={"*"},
        feedback={"write"},
        providers={"read"},
        contexts={"*"},
        mcp_providers={"read"},
        mcp_tools={"read"},
        mcp_proxy={"*"},
    ),
}
ROLE_PERMISSIONS[UserRole.developer] = ROLE_PERMISSIONS[UserRole.user] | Permissions(
    providers={"read", "write"},  # TODO provider ownership
    mcp_providers={"read", "write"},
)


class ParsedToken(BaseModel):
    global_permissions: Permissions
    context_permissions: Permissions
    context_id: UUID
    user_id: UUID
    raw: dict[str, Any]


def issue_internal_jwt(
    user_id: UUID,
    context_id: UUID,
    global_permissions: Permissions,
    context_permissions: Permissions,
    configuration: Configuration,
) -> tuple[str, AwareDatetime]:
    assert configuration.auth.jwt_secret_key
    secret_key = configuration.auth.jwt_secret_key.get_secret_value()
    now = utc_now()
    expires_at = now + timedelta(minutes=20)
    payload = {
        "context_id": str(context_id),
        "sub": str(user_id),
        "exp": expires_at,
        "iat": now,
        "iss": "beeai-server",
        "aud": "beeai-server",  # the token is for ourselves, noone else should consume it
        "resource": [f"context:{context_id}"],
        "scope": {
            "global": global_permissions.model_dump(mode="json"),
            "context": context_permissions.model_dump(mode="json"),
        },
    }
    return jwt.encode(payload, secret_key, algorithm="HS256"), expires_at


def verify_internal_jwt(token: str, configuration: Configuration) -> ParsedToken:
    assert configuration.auth.jwt_secret_key
    secret_key = configuration.auth.jwt_secret_key.get_secret_value()
    payload = jwt.decode(token, secret_key, algorithms=["HS256"], audience="beeai-server", issuer="beeai-server")
    context_id = UUID(payload["resource"][0].replace("context:", ""))
    return ParsedToken(
        global_permissions=Permissions.model_validate(payload["scope"]["global"]),
        context_permissions=Permissions.model_validate(payload["scope"]["context"]),
        context_id=context_id,
        user_id=UUID(payload["sub"]),
        raw=payload,
    )
