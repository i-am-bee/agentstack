# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from datetime import timedelta
from uuid import UUID

import jwt
from kink import inject

from beeai_server.configuration import Configuration
from beeai_server.domain.models.user import User
from beeai_server.service_layer.services.users import UserService
from beeai_server.utils.utils import utc_now


@inject
def issue_token(user: User, configuration: Configuration) -> str:
    # TODO: using admin password as secret_key - should we use a dedicated secret?
    secret_key = configuration.auth.admin_password.get_secret_value()
    now = utc_now()
    payload = {"user_id": str(user.id), "role": "user", "exp": now + timedelta(hours=1), "iat": now}
    return jwt.encode(payload, secret_key, algorithm="HS256")


@inject
async def verify_token(token: str, configuration: Configuration, user_service: UserService) -> User:
    # TODO: using admin password as secret_key - should we use a dedicated secret?
    secret_key = configuration.auth.admin_password.get_secret_value()
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return await user_service.get_user(user_id=UUID(payload["user_id"]))
    except jwt.ExpiredSignatureError:
        raise Exception("Token expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")
