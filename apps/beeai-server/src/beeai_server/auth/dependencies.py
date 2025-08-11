# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyCookie, APIKeyHeader
from kink import di

from beeai_server.auth.utils import decode_jwt_token, extract_token
from beeai_server.configuration import Configuration
from beeai_server.domain.models.user import User, UserRole
from beeai_server.exceptions import EntityNotFoundError
from beeai_server.service_layer.services.users import UserService

ConfigurationDependency = Annotated[Configuration, Depends(lambda: di[Configuration])]
UserServiceDependency = Annotated[UserService, Depends(lambda: di[UserService])]

api_key_cookie = APIKeyCookie(name="beeai-platform", auto_error=False)
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


async def get_authenticated_user(
    user_service: UserServiceDependency,
    configuration: ConfigurationDependency,
    cookie_token: Annotated[str | None, Security(api_key_cookie)],
    header_token: Annotated[str | None, Security(api_key_header)],
) -> User:
    if configuration.oidc.disable_oidc:
        # Bypass OIDC validation — return a default user for dev/testing mode
        return await user_service.get_user_by_email("admin@beeai.dev")
    try:
        token = extract_token(header_token, cookie_token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Authorization header: {e}",
        ) from e
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    claims = decode_jwt_token(token)
    if not claims:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    email = claims.get("email")
    is_admin = email in configuration.oidc.admin_emails

    try:
        authenticated_user = await user_service.get_user_by_email(email=email)
    except EntityNotFoundError:
        role = UserRole.admin if is_admin else UserRole.user
        authenticated_user = await user_service.create_user(email=email, role=role)

    return authenticated_user


def check_admin(user: Annotated[User, Depends(get_authenticated_user)]) -> User:
    if user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return user


AuthenticatedUserDependency = Annotated[User, Depends(get_authenticated_user)]
AdminUserDependency = Annotated[str, Depends(check_admin)]
