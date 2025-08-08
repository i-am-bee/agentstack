# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBasic, HTTPBasicCredentials, HTTPBearer
from jwt import PyJWTError
from kink import di
from pydantic import ConfigDict

from beeai_server.api.auth import ROLE_PERMISSIONS, verify_internal_jwt
from beeai_server.configuration import Configuration
from beeai_server.domain.models.permissions import AuthorizedUser, Permissions
from beeai_server.domain.models.user import User, UserRole
from beeai_server.service_layer.services.a2a import A2AProxyService
from beeai_server.service_layer.services.contexts import ContextService
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
ContextServiceDependency = Annotated[ContextService, Depends(lambda: di[ContextService])]
EnvServiceDependency = Annotated[EnvService, Depends(lambda: di[EnvService])]
FileServiceDependency = Annotated[FileService, Depends(lambda: di[FileService])]
UserServiceDependency = Annotated[UserService, Depends(lambda: di[UserService])]
VectorStoreServiceDependency = Annotated[VectorStoreService, Depends(lambda: di[VectorStoreService])]
UserFeedbackServiceDependency = Annotated[UserFeedbackService, Depends(lambda: di[UserFeedbackService])]


async def authorized_user(
    user_service: UserServiceDependency,
    configuration: ConfigurationDependency,
    basic_auth: Annotated[HTTPBasicCredentials | None, Depends(HTTPBasic(auto_error=False))],
    bearer_auth: Annotated[HTTPAuthorizationCredentials | None, Depends(HTTPBearer(auto_error=False))],
) -> AuthorizedUser:
    """
    TODO: authentication is not impelemented yet, for now, this always returns the dummy user.
    """
    if bearer_auth:
        # Check Bearer token first - locally this allows for "checking permissions" for development purposes
        # even if auth is disabled (requests that would pass with no header may not pass with context token header)
        try:
            parsed_token = verify_internal_jwt(bearer_auth.credentials, configuration=configuration)
            user = await user_service.get_user(parsed_token.user_id)
            return AuthorizedUser(
                user=user,
                global_permissions=parsed_token.global_permissions,
                context_permissions=parsed_token.context_permissions,
                context_id=parsed_token.context_id,
            )
        except PyJWTError:
            raise NotImplementedError("Oauth is not implemented yet.") from None

    if configuration.auth.disable_auth or (
        basic_auth and basic_auth.password == configuration.auth.admin_password.get_secret_value()
    ):
        user = await user_service.get_user_by_email("admin@beeai.dev")
        return AuthorizedUser(
            user=user,
            global_permissions=ROLE_PERMISSIONS[user.role],
            context_permissions=ROLE_PERMISSIONS[user.role],
            context_id=None,
        )

    user = await user_service.get_user_by_email("user@beeai.dev")
    return AuthorizedUser(
        user=user,
        global_permissions=ROLE_PERMISSIONS[user.role],
        context_permissions=ROLE_PERMISSIONS[user.role],
        context_id=None,
    )


def admin_auth(user: Annotated[User, Depends(authorized_user)]) -> User:
    if user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


class RequiresContextPermissions(Permissions):
    model_config = ConfigDict(frozen=True)

    def __call__(
        self,
        user: Annotated[AuthorizedUser, Depends(authorized_user)],
        context_id: Annotated[UUID | None, Query()] = None,
    ) -> AuthorizedUser:
        # check if context_id matches token
        if user.context_id and context_id and user.context_id != context_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Token context id does not match request token id: {context_id}",
            )

        # check permissions if in context
        if context_id and (user.context_permissions | user.global_permissions).check(self):
            if not user.context_id:
                # user did not use context token to sign in but set the context_id query param, so we set it explicitly:
                user.context_id = context_id
            return user

        # check permissions if outside of context
        if not context_id and user.global_permissions.check(self):
            return user

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")


class RequiresPermissions(Permissions):
    model_config = ConfigDict(frozen=True)

    def __call__(self, user: Annotated[AuthorizedUser, Depends(authorized_user)]) -> AuthorizedUser:
        if user.global_permissions.check(self):
            return user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
