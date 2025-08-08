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
    UserRole.developer: Permissions(
        files={"*"},
        vector_stores={"*"},
        llm={"*"},
        feedback={"write"},
        embeddings={"*"},
        a2a_proxy={"*"},
        providers={"read", "write"},  # TODO provider ownership
    ),
    UserRole.user: Permissions(
        files={"*"},
        vector_stores={"*"},
        llm={"*"},
        embeddings={"*"},
        a2a_proxy={"*"},
        feedback={"write"},
        providers={"read"},
    ),
}


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
        "user_id": str(user_id),
        "context_id": str(context_id),
        "exp": expires_at,
        "iat": now,
        "permissions": {
            "global": global_permissions.model_dump(mode="json"),
            "context": context_permissions.model_dump(mode="json"),
        },
    }
    return jwt.encode(payload, secret_key, algorithm="HS256"), expires_at


def verify_internal_jwt(token: str, configuration: Configuration) -> ParsedToken:
    assert configuration.auth.jwt_secret_key
    secret_key = configuration.auth.jwt_secret_key.get_secret_value()
    payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    return ParsedToken(
        global_permissions=Permissions.model_validate(payload["permissions"]["global"]),
        context_permissions=Permissions.model_validate(payload["permissions"]["context"]),
        context_id=UUID(payload["context_id"]),
        user_id=UUID(payload["user_id"]),
        raw=payload,
    )
