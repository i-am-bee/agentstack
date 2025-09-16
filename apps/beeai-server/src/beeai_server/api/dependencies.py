# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Path, Query, Request, Security, status
from fastapi.security import APIKeyCookie, HTTPAuthorizationCredentials, HTTPBasic, HTTPBasicCredentials, HTTPBearer
from jwt import PyJWTError
from kink import di
from pydantic import ConfigDict

from beeai_server.api.auth import (
    ROLE_PERMISSIONS,
    decode_oauth_jwt_or_introspect,
    extract_oauth_token,
    fetch_user_info,
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
api_key_cookie = APIKeyCookie(name="beeai-platform", auto_error=False)


async def authenticate_oauth_user(
    bearer_auth: HTTPAuthorizationCredentials,
    cookie_auth: str | None,
    user_service: UserServiceDependency,
    configuration: ConfigurationDependency,
    request: Request,
) -> AuthorizedUser:
    """
    Authenticate using an OIDC/OAuth2 JWT bearer token with JWKS.
    Creates the user if it doesn't exist.
    """
    try:
        token = extract_oauth_token(bearer_auth, cookie_auth)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Authorization header: {e}",
        ) from e

    expected_audience = str(request.url.replace(path="/"))
    claims, issuer = await decode_oauth_jwt_or_introspect(
        token=token, jwks_dict=di["JWKS_CACHE"], aud=expected_audience, configuration=configuration
    )
    if not claims:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    email = claims.get("email")
    if not email:
        provider = next((p for p in configuration.auth.oidc.providers if str(p.issuer) == str(issuer)), None)
        if not provider:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"issuer not configured. {issuer}")
        userinfo = await fetch_user_info(token, f"{provider.issuer!s}/userinfo")
        email = userinfo.get("email")
        email_verified = userinfo.get("email_verified", False)
    else:
        email_verified = claims.get("email_verified", False)

    if not email or not email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Verified email not available in token or userinfo"
        )

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
    cookie_auth: Annotated[str | None, Security(api_key_cookie)],
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
        except PyJWTError:
            if configuration.auth.oidc.enabled:
                return await authenticate_oauth_user(bearer_auth, cookie_auth, user_service, configuration, request)
            # TODO: update agents
            logger.warning("Bearer token is invalid, agent is not probably not using llm extension correctly")

    if configuration.auth.oidc.enabled and cookie_auth:
        return await authenticate_oauth_user(bearer_auth, cookie_auth, user_service, configuration, request)

    if configuration.auth.basic.enabled:
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
