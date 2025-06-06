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

from typing import Annotated

from fastapi.security import HTTPBasicCredentials, HTTPBasic
from fastapi import status, HTTPException

from beeai_server.configuration import Configuration
from beeai_server.domain.models.user import User, UserRole
from beeai_server.service_layer.services.acp import AcpProxyService
from beeai_server.service_layer.services.env import EnvService
from beeai_server.service_layer.services.files import FileService
from beeai_server.service_layer.services.provider import ProviderService
from beeai_server.service_layer.services.users import UserService
from fastapi import Depends
from kink import di


ConfigurationDependency = Annotated[Configuration, Depends(lambda: di[Configuration])]
ProviderServiceDependency = Annotated[ProviderService, Depends(lambda: di[ProviderService])]
AcpProxyServiceDependency = Annotated[AcpProxyService, Depends(lambda: di[AcpProxyService])]
EnvServiceDependency = Annotated[EnvService, Depends(lambda: di[EnvService])]
FileServiceDependency = Annotated[FileService, Depends(lambda: di[FileService])]
UserServiceDependency = Annotated[UserService, Depends(lambda: di[UserService])]

# Auth


async def authenticated_user(
    user_service: UserServiceDependency,
    configuration: ConfigurationDependency,
    basic_auth: Annotated[HTTPBasicCredentials | None, Depends(HTTPBasic(auto_error=False))],
) -> User:
    """
    TODO: authentication is not impelemented yet, for now, this always returns the dummy user.
    """
    if configuration.auth.disable_auth:
        return await user_service.get_user_by_email("admin@beeai.dev")

    if basic_auth and basic_auth.password == configuration.auth.admin_password.get_secret_value():
        return await user_service.get_user_by_email("admin@beeai.dev")

    return await user_service.get_user_by_email("user@beeai.dev")


def admin_auth(
    user: Annotated[User, Depends(authenticated_user)],
) -> User:
    if user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


AuthenticatedUserDependency = Annotated[User, Depends(authenticated_user)]
AdminUserDependency = Annotated[str, Depends(admin_auth)]
