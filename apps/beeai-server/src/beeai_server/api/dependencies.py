# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from kink import di

from beeai_server.configuration import Configuration
from beeai_server.domain.models.user import User, UserRole
from beeai_server.service_layer.services.a2a import A2AProxyService
from beeai_server.service_layer.services.env import EnvService
from beeai_server.service_layer.services.files import FileService
from beeai_server.service_layer.services.mcp import McpService
from beeai_server.service_layer.services.provider import ProviderService
from beeai_server.service_layer.services.user_feedback import UserFeedbackService
from beeai_server.service_layer.services.users import UserService
from beeai_server.service_layer.services.vector_stores import VectorStoreService

ConfigurationDependency = Annotated[Configuration, Depends(lambda: di[Configuration])]
ProviderServiceDependency = Annotated[ProviderService, Depends(lambda: di[ProviderService])]
A2AProxyServiceDependency = Annotated[A2AProxyService, Depends(lambda: di[A2AProxyService])]
McpServiceDependency = Annotated[McpService, Depends(lambda: di[McpService])]
EnvServiceDependency = Annotated[EnvService, Depends(lambda: di[EnvService])]
FileServiceDependency = Annotated[FileService, Depends(lambda: di[FileService])]
UserServiceDependency = Annotated[UserService, Depends(lambda: di[UserService])]
VectorStoreServiceDependency = Annotated[VectorStoreService, Depends(lambda: di[VectorStoreService])]
UserFeedbackServiceDependency = Annotated[UserFeedbackService, Depends(lambda: di[UserFeedbackService])]

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


def admin_auth(user: Annotated[User, Depends(authenticated_user)]) -> User:
    if user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


AuthenticatedUserDependency = Annotated[User, Depends(authenticated_user)]
AdminUserDependency = Annotated[str, Depends(admin_auth)]
