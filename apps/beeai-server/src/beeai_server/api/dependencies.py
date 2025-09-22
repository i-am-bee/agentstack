# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Annotated
from uuid import UUID

from authlib.jose import JoseError
from fastapi import Depends, HTTPException, Path, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBasic, HTTPBasicCredentials, HTTPBearer
from kink import di
from pydantic import ConfigDict

from beeai_server.api.auth.auth import (
    ROLE_PERMISSIONS,
    extract_oauth_token,
    get_user_info,
    validate_oauth_access_token,
    verify_internal_jwt,
)
from beeai_server.configuration import Configuration
from beeai_server.domain.models.permissions import AuthorizedUser, Permissions
from beeai_server.domain.models.user import UserRole
from beeai_server.exceptions import EntityNotFoundError
from beeai_server.service_layer.services.a2a import A2AProxyService
from beeai_server.service_layer.services.auth import AuthService
from beeai_server.service_layer.services.configurations import ConfigurationService
from beeai_server.service_layer.services.contexts import ContextService
from beeai_server.service_layer.services.files import FileService
from beeai_server.service_layer.services.mcp import McpService
from beeai_server.service_layer.services.model_provider import ModelProviderService
from beeai_server.service_layer.services.provider import ProviderService
from beeai_server.service_layer.services.user_feedback import UserFeedbackService
from beeai_server.service_layer.services.users import UserService
from beeai_server.service_layer.services.vector_stores import VectorStoreService

ConfigurationDependency = Annotated[Configuration, Depends(lambda: di[Configuration])]
ProviderServiceDependency = Annotated[ProviderService, Depends(lambda: di[ProviderService])]
A2AProxyServiceDependency = Annotated[A2AProxyService, Depends(lambda: di[A2AProxyService])]
McpServiceDependency = Annotated[McpService, Depends(lambda: di[McpService])]
ContextServiceDependency = Annotated[ContextService, Depends(lambda: di[ContextService])]
ConfigurationServiceDependency = Annotated[ConfigurationService, Depends(lambda: di[ConfigurationService])]
FileServiceDependency = Annotated[FileService, Depends(lambda: di[FileService])]
UserServiceDependency = Annotated[UserService, Depends(lambda: di[UserService])]
VectorStoreServiceDependency = Annotated[VectorStoreService, Depends(lambda: di[VectorStoreService])]
UserFeedbackServiceDependency = Annotated[UserFeedbackService, Depends(lambda: di[UserFeedbackService])]
AuthServiceDependency = Annotated[AuthService, Depends(lambda: di[AuthService])]
ModelProviderServiceDependency = Annotated[ModelProviderService, Depends(lambda: di[ModelProviderService])]

logger = logging.getLogger(__name__)


async def authenticate_oauth_user(
    bearer_auth: HTTPAuthorizationCredentials,
    user_service: UserServiceDependency,
    configuration: ConfigurationDependency,
    request: Request,
) -> AuthorizedUser:
    """
    Authenticate using an OIDC/OAuth2 JWT bearer token with JWKS.
    Creates the user if it doesn't exist.
    """
    try:
        token = extract_oauth_token(bearer_auth)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Authorization header: {e}",
        ) from e

    expected_audience = str(request.url.replace(path="/"))
    try:
        claims, provider = await validate_oauth_access_token(
            token=token, aud=expected_audience, configuration=configuration
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token validation failed") from e

    try:
        claims = (
            claims
            if claims and "email" in claims and "email_verified" in claims
            else await get_user_info(token, provider=provider)
        )
        email = claims.get("email")
        email_verified = claims.get("email_verified")
        if not isinstance(email, str) or not isinstance(email_verified, (str, bool)) or not bool(email_verified):
            raise RuntimeError("Email not verified")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Verified email not found") from e

    is_admin = email.lower() in configuration.auth.oidc.admin_emails

    try:
        user = await user_service.get_user_by_email(email=email)
    except EntityNotFoundError:
        role = UserRole.ADMIN if is_admin else configuration.auth.oidc.default_new_user_role
        user = await user_service.create_user(email=email, role=role)

    return AuthorizedUser(
        user=user,
        global_permissions=ROLE_PERMISSIONS[user.role],
        context_permissions=ROLE_PERMISSIONS[user.role],
    )


async def authorized_user(
    user_service: UserServiceDependency,
    configuration: ConfigurationDependency,
    basic_auth: Annotated[HTTPBasicCredentials | None, Depends(HTTPBasic(auto_error=False))],
    bearer_auth: Annotated[HTTPAuthorizationCredentials | None, Depends(HTTPBearer(auto_error=False))],
    request: Request,
) -> AuthorizedUser:
    if bearer_auth:
        # Check Bearer token first - locally this allows for "checking permissions" for development purposes
        # even if auth is disabled (requests that would pass with no header may not pass with context token header)
        try:
            parsed_token = verify_internal_jwt(bearer_auth.credentials, configuration=configuration)
            user = await user_service.get_user(parsed_token.user_id)
            token = AuthorizedUser(
                user=user,
                global_permissions=parsed_token.global_permissions,
                context_permissions=parsed_token.context_permissions,
                token_context_id=parsed_token.context_id,
            )
            return token
        except JoseError:
            if configuration.auth.oidc.enabled:
                return await authenticate_oauth_user(bearer_auth, user_service, configuration, request)
            # TODO: update agents
            logger.warning("Bearer token is invalid, agent is not probably not using llm extension correctly")

    if configuration.auth.oidc.enabled:
        if not bearer_auth:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token not found")
        return await authenticate_oauth_user(bearer_auth, user_service, configuration, request)

    if configuration.auth.basic.enabled:
        assert configuration.auth.basic.admin_password is not None
        if basic_auth and basic_auth.password == configuration.auth.basic.admin_password.get_secret_value():
            user = await user_service.get_user_by_email("admin@beeai.dev")
            return AuthorizedUser(
                user=user,
                global_permissions=ROLE_PERMISSIONS[user.role],
                context_permissions=ROLE_PERMISSIONS[user.role],
            )
        else:
            user = await user_service.get_user_by_email("user@beeai.dev")
            return AuthorizedUser(
                user=user,
                global_permissions=ROLE_PERMISSIONS[user.role],
                context_permissions=ROLE_PERMISSIONS[user.role],
            )

    if configuration.auth.disable_auth:
        user = await user_service.get_user_by_email("admin@beeai.dev")
        return AuthorizedUser(
            user=user,
            global_permissions=ROLE_PERMISSIONS[user.role],
            context_permissions=ROLE_PERMISSIONS[user.role],
        )
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


class RequiresContextPermissions(Permissions):
    model_config = ConfigDict(frozen=True)

    def __call__(
        self,
        user: Annotated[AuthorizedUser, Depends(authorized_user)],
        context_id: Annotated[UUID | None, Query()] = None,
    ) -> AuthorizedUser:
        # check if context_id matches token
        if user.token_context_id and context_id and user.token_context_id != context_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Token context id does not match request token id: {context_id}",
            )
        user.context_id = context_id

        # check permissions if in context
        if context_id and (user.context_permissions | user.global_permissions).check(self):
            return user

        # check permissions if outside of context
        if not context_id and user.global_permissions.check(self):
            return user

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")


class RequiresContextPermissionsPath(RequiresContextPermissions):
    def __call__(  # pyright: ignore [reportIncompatibleMethodOverride]
        self,
        user: Annotated[AuthorizedUser, Depends(authorized_user)],
        context_id: Annotated[UUID, Path()],
    ) -> AuthorizedUser:
        return super().__call__(user=user, context_id=context_id)


class RequiresPermissions(Permissions):
    model_config = ConfigDict(frozen=True)

    def __call__(self, user: Annotated[AuthorizedUser, Depends(authorized_user)]) -> AuthorizedUser:
        if user.global_permissions.check(self):
            return user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
