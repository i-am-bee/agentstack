# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
import os
from datetime import timedelta
from urllib.parse import urljoin

from a2a.auth.user import User
from async_lru import alru_cache
from authlib.jose import JsonWebKey, JWTClaims, KeySet, jwt
from authlib.jose.errors import JoseError
from fastapi import Request
from fastapi.security import HTTPBearer
from pydantic import Secret
from starlette.authentication import (
    AuthCredentials,
    AuthenticationBackend,
    AuthenticationError,
    BaseUser,
)
from starlette.requests import HTTPConnection
from typing_extensions import override

from agentstack_sdk.platform import use_platform_client
from agentstack_sdk.types import JsonValue

logger = logging.getLogger(__name__)


class PlatformAuthenticatedUser(User, BaseUser):
    def __init__(self, claims: dict[str, JsonValue], auth_token: str):
        self.claims: dict[str, JsonValue] = claims
        self.auth_token: Secret[str] = Secret(auth_token)

    @property
    @override
    def is_authenticated(self) -> bool:
        return True

    @property
    @override
    def user_name(self) -> str:
        sub = self.claims.get("sub", None)
        assert sub and isinstance(sub, str)
        return sub

    @property
    @override
    def display_name(self) -> str:
        name = self.claims.get("name", None)
        assert name and isinstance(name, str)
        return name

    @property
    @override
    def identity(self) -> str:
        return self.user_name


@alru_cache(ttl=timedelta(minutes=15).seconds)
async def discover_jwks() -> KeySet:
    try:
        async with use_platform_client() as client:
            response = await client.get("/.well-known/jwks")
            return JsonWebKey.import_key_set(response.raise_for_status().json())  # pyright: ignore[reportAny]
    except Exception as e:
        url = "{platform_url}/.well-known/jwks"
        logger.warning(f"JWKS discovery failed for url {url}: {e}")
        raise RuntimeError(f"JWKS discovery failed for url {url}") from e


class PlatformAuthBackend(AuthenticationBackend):
    def __init__(self, public_url: str | None = None, skip_audience_validation: bool | None = None) -> None:
        self.skip_audience_validation: bool = (
            skip_audience_validation
            if skip_audience_validation is not None
            else os.getenv("PLATFORM_AUTH__SKIP_AUDIENCE_VALIDATION", "false").lower() in ("true", "1")
        )
        self._audience: str | None = public_url or os.getenv("PLATFORM_AUTH__PUBLIC_URL", None)
        if not self.skip_audience_validation and not self._audience:
            logger.warning(
                "Public URL is not provided and audience validation is enabled. Proceeding to check audience from the request target URL. "
                + "This may not work when requests to agents are proxied. (hint: set PLATFORM_AUTH__PUBLIC_URL env variable)"
            )

        self.security: HTTPBearer = HTTPBearer(auto_error=False)

    @override
    async def authenticate(self, conn: HTTPConnection) -> tuple[AuthCredentials, BaseUser] | None:
        # We construct a Request object from the scope for compatibility with HTTPBearer and logging
        request = Request(scope=conn.scope)

        if request.url.path in ["/healthcheck", "/.well-known/agent-card.json"]:
            return None

        if not (auth := await self.security(request)):
            raise AuthenticationError("Missing Authorization header")

        audiences: list[str] = []
        if not self.skip_audience_validation:
            if self._audience:
                audiences = [urljoin(self._audience, path) for path in ["/", "/jsonrpc"]]
            else:
                audiences = [str(request.url.replace(path=path)) for path in ["/", "/jsonrpc"]]

        try:
            # check only hostname urljoin("http://host:port/a/b", "/") -> "http://host:port/"
            jwks = await discover_jwks()

            # Verify signature
            claims: JWTClaims = jwt.decode(
                auth.credentials,
                jwks,
                claims_options={
                    "sub": {"essential": True},
                    "exp": {"essential": True},
                    # "iss": {"essential": True}, # Issuer validation might be tricky if internal/external URLs differ
                }
                | ({"aud": {"essential": True, "values": audiences}} if not self.skip_audience_validation else {}),
            )
            claims.validate()

            return AuthCredentials(["authenticated"]), PlatformAuthenticatedUser(claims, auth.credentials)

        except (ValueError, JoseError) as e:
            logger.warning(f"Authentication failed: {e}")
            raise AuthenticationError("Invalid token") from e
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise AuthenticationError(f"Authentication failed: {e}") from e
