# Copyright 2025 © BeeAI a Series of LF Projects, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
