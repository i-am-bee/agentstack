# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Annotated, Final
from uuid import UUID

from fastapi import Depends, HTTPException, Path, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBasic, HTTPBasicCredentials, HTTPBearer
from kink import di
from limits.aio.storage import Storage
from pydantic import ConfigDict

from agentstack_server.api.auth.auth import (
    ROLE_PERMISSIONS,
    extract_oauth_token,
    get_user_info,
    validate_basic_auth,
    validate_oauth_access_token,
    verify_internal_jwt,
)
from agentstack_server.api.auth.utils import create_resource_uri
from agentstack_server.api.rate_limiter import RateLimit, UserRateLimiter
from agentstack_server.configuration import Configuration
from agentstack_server.domain.models.permissions import AuthorizedUser, Permissions
from agentstack_server.domain.models.user import UserRole
from agentstack_server.exceptions import EntityNotFoundError
from agentstack_server.service_layer.services.a2a import A2AProxyService
from agentstack_server.service_layer.services.auth import AuthService
from agentstack_server.service_layer.services.configurations import ConfigurationService
from agentstack_server.service_layer.services.connector import ConnectorService
from agentstack_server.service_layer.services.contexts import ContextService
from agentstack_server.service_layer.services.external_mcp_service import ExternalMcpService
from agentstack_server.service_layer.services.files import FileService
from agentstack_server.service_layer.services.model_providers import ModelProviderService
from agentstack_server.service_layer.services.provider_build import ProviderBuildService
from agentstack_server.service_layer.services.providers import ProviderService
from agentstack_server.service_layer.services.user_feedback import UserFeedbackService
from agentstack_server.service_layer.services.users import UserService
from agentstack_server.service_layer.services.vector_stores import VectorStoreService

ConfigurationDependency = Annotated[Configuration, Depends(lambda: di[Configuration])]
ProviderServiceDependency = Annotated[ProviderService, Depends(lambda: di[ProviderService])]
ProviderBuildServiceDependency = Annotated[ProviderBuildService, Depends(lambda: di[ProviderBuildService])]
A2AProxyServiceDependency = Annotated[A2AProxyService, Depends(lambda: di[A2AProxyService])]
ContextServiceDependency = Annotated[ContextService, Depends(lambda: di[ContextService])]
ConfigurationServiceDependency = Annotated[ConfigurationService, Depends(lambda: di[ConfigurationService])]
FileServiceDependency = Annotated[FileService, Depends(lambda: di[FileService])]
UserServiceDependency = Annotated[UserService, Depends(lambda: di[UserService])]
VectorStoreServiceDependency = Annotated[VectorStoreService, Depends(lambda: di[VectorStoreService])]
UserFeedbackServiceDependency = Annotated[UserFeedbackService, Depends(lambda: di[UserFeedbackService])]
AuthServiceDependency = Annotated[AuthService, Depends(lambda: di[AuthService])]
ModelProviderServiceDependency = Annotated[ModelProviderService, Depends(lambda: di[ModelProviderService])]
ConnectorServiceDependency = Annotated[ConnectorService, Depends(lambda: di[ConnectorService])]
ExternalMcpServiceDependency = Annotated[ExternalMcpService, Depends(lambda: di[ExternalMcpService])]

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

    expected_aud: set[str] = set()
    if configuration.auth.oidc.validate_audience:
        base_url = request.url.replace(path="/")
        expected_aud.add(create_resource_uri(base_url))
        if base_url.hostname in {"localhost", "127.0.0.1"}:  # make localhost and 127.0.0.1 interchangeable
            expected_aud |= {
                create_resource_uri(base_url.replace(hostname="localhost")),
                create_resource_uri(base_url.replace(hostname="127.0.0.1")),
            }

    try:
        claims, provider = await validate_oauth_access_token(token=token, aud=expected_aud, configuration=configuration)
    except Exception as e:
        logger.warning(f"Token validation failed: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token validation failed") from e

    realm_access = claims.get("realm_access", {}) if claims else {}
    realm_roles = realm_access.get("roles", []) if realm_access else []

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

    calculated_role = UserRole.USER
    if "agentstack-admin" in realm_roles:
        calculated_role = UserRole.ADMIN
    elif "agentstack-developer" in realm_roles:
        calculated_role = UserRole.DEVELOPER

    try:
        user = await user_service.get_user_by_email(email=email)
    except EntityNotFoundError:
        user = await user_service.create_user(email=email)

    user.role = calculated_role
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
    # 1. Check internal JWT
    if bearer_auth:
        # Check Context token first - locally this allows for "checking permissions" for development purposes
        # even if auth is disabled (requests that would pass with no header may not pass with context token header)
        try:
            parsed_token = verify_internal_jwt(bearer_auth.credentials, configuration=configuration)
            user = await user_service.get_user(parsed_token.user_id)

            return AuthorizedUser(
                user=user,
                global_permissions=parsed_token.global_permissions,
                context_permissions=parsed_token.context_permissions,
                token_context_id=parsed_token.context_id,
            )
        except Exception as e:
            if configuration.auth.disable_auth:
                logger.warning(f"Context token validation failed: {e}")

    # 2. Return admin user if auth is disabled
    if configuration.auth.disable_auth:
        user = await user_service.get_user_by_email("admin@beeai.dev")
        user.role = UserRole.ADMIN
        return AuthorizedUser(
            user=user,
            global_permissions=ROLE_PERMISSIONS[user.role],
            context_permissions=ROLE_PERMISSIONS[user.role],
        )

    # 3. Check basic auth header
    if configuration.auth.basic.enabled and basic_auth:
        try:  # get access_token and continue with bearer_auth
            access_token = await validate_basic_auth(basic_auth.username, basic_auth.password, configuration)
            bearer_auth = HTTPAuthorizationCredentials(scheme="Bearer", credentials=access_token)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials") from e

    # 4. Check OIDC token
    if bearer_auth:
        return await authenticate_oauth_user(bearer_auth, user_service, configuration, request)

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


def user_rate_limiter(
    user: Annotated[AuthorizedUser, Depends(authorized_user)],
    configuration: ConfigurationDependency,
    storage: Annotated[Storage, Depends(lambda: di[Storage])],
) -> UserRateLimiter:
    return UserRateLimiter(user=user.user, configuration=configuration, storage=storage)


UserRateLimiterDependency = Annotated[UserRateLimiter, Depends(user_rate_limiter)]


class ActivatedUserRateLimiterDependency:
    def __init__(self, limit: RateLimit) -> None:
        self._limit: Final[RateLimit] = limit

    async def __call__(self, user_rate_limiter: UserRateLimiterDependency) -> UserRateLimiter:
        await user_rate_limiter.hit(self._limit)
        return user_rate_limiter
