# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Query, Security, status
from fastapi.security import APIKeyCookie, HTTPAuthorizationCredentials, HTTPBasic, HTTPBasicCredentials, HTTPBearer
from jwt import PyJWTError
from kink import di
from pydantic import ConfigDict

from beeai_server.api.auth import (
    JWKS_DICT,
    ROLE_PERMISSIONS,
    decode_oauth_jwt_or_introspect,
    extract_oauth_token,
    fetch_user_info,
    verify_internal_jwt,
)
from beeai_server.configuration import Configuration
from beeai_server.domain.models.permissions import AuthorizedUser, Permissions
from beeai_server.domain.models.user import User, UserRole
from beeai_server.exceptions import EntityNotFoundError
from beeai_server.service_layer.services.a2a import A2AProxyService
from beeai_server.service_layer.services.auth import AuthService
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
AuthServiceDependency = Annotated[AuthService, Depends(lambda: di[AuthService])]

logger = logging.getLogger(__name__)
api_key_cookie = APIKeyCookie(name="beeai-platform", auto_error=False)


async def authenticate_oauth_user(
    bearer_auth: HTTPAuthorizationCredentials,
    cookie_auth: str | None,
    user_service: UserServiceDependency,
    configuration: ConfigurationDependency,
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

    claims, issuer = await decode_oauth_jwt_or_introspect(
        token, jwks_dict=di[JWKS_DICT], aud="beeai-server", configuration=configuration
    )
    if not claims:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    email = claims.get("email")
    if not email:
        provider = next((p for p in configuration.auth.oidc.providers if p.issuer == issuer), None)
        if not provider:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="issuer not configured")
        userinfo = await fetch_user_info(token, f"{provider.issuer}/userinfo")
        email = userinfo.get("email")

    if not email:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not available in token or userinfo")

    is_admin = email in configuration.auth.oidc.admin_emails

    try:
        user = await user_service.get_user_by_email(email=email)
    except EntityNotFoundError:
        role = UserRole.admin if is_admin else UserRole.user
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
) -> AuthorizedUser:
    # 1. If auth is disabled, return admin user
    if configuration.auth.disable_auth:
        logger.warning("Authentication is disabled. Returning admin user.")
        user = await user_service.get_user_by_email("admin@beeai.dev")
        return AuthorizedUser(
            user=user,
            global_permissions=ROLE_PERMISSIONS[user.role],
            context_permissions=ROLE_PERMISSIONS[user.role],
        )

    # 2. OIDC is enabled, try Bearer token
    if not configuration.auth.oidc.disable_oidc:
        if bearer_auth:
            try:
                parsed_token = verify_internal_jwt(bearer_auth.credentials, configuration=configuration)
                user = await user_service.get_user(parsed_token.user_id)
                token = AuthorizedUser(
                    user=user,
                    global_permissions=parsed_token.global_permissions,
                    context_permissions=parsed_token.context_permissions,
                    token_context_id=parsed_token.context_id,
                )
                logger.info("Token is valid!")
                return token
            except PyJWTError:
                try:
                    return await authenticate_oauth_user(bearer_auth, cookie_auth, user_service, configuration)
                except Exception as e:
                    logger.error(f"OIDC authentication failed: {e}")
                    raise RuntimeError("OIDC authentication failed.") from e
        else:
            raise RuntimeError("No bearer token provided")

    # 3. Basic auth, fallback only if OIDC is disabled
    if not configuration.auth.basic.disable_basic and basic_auth:
        expected_password = configuration.auth.basic.admin_password.get_secret_value()
        if basic_auth.password == expected_password:
            user = await user_service.get_user_by_email("admin@beeai.dev")
            return AuthorizedUser(
                user=user,
                global_permissions=ROLE_PERMISSIONS[user.role],
                context_permissions=ROLE_PERMISSIONS[user.role],
            )

    user = await user_service.get_user_by_email("user@beeai.dev")
    return AuthorizedUser(
        user=user,
        global_permissions=ROLE_PERMISSIONS[user.role],
        context_permissions=ROLE_PERMISSIONS[user.role],
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


class RequiresPermissions(Permissions):
    model_config = ConfigDict(frozen=True)

    def __call__(self, user: Annotated[AuthorizedUser, Depends(authorized_user)]) -> AuthorizedUser:
        if user.global_permissions.check(self):
            return user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
