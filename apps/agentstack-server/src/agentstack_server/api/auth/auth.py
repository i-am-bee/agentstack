# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import UUID

import httpx
from async_lru import alru_cache
from authlib.jose import JWTClaims, jwt
from authlib.jose.errors import DecodeError, KeyMismatchError
from authlib.jose.rfc7517 import JsonWebKey, KeySet
from authlib.oauth2.rfc7662 import IntrospectTokenValidator
from authlib.oauth2.rfc8414 import AuthorizationServerMetadata
from authlib.oauth2.rfc8414 import get_well_known_url as oauth_get_well_known_url
from authlib.oidc.discovery import OpenIDProviderMetadata
from authlib.oidc.discovery import get_well_known_url as oidc_get_well_known_url
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import AwareDatetime, BaseModel

from agentstack_server.api.auth.errors import (
    IntrospectionDiscoveryError,
    IssuerDiscoveryError,
    JWKSDiscoveryError,
    UserInfoDiscoveryError,
)
from agentstack_server.configuration import Configuration, OidcProvider
from agentstack_server.domain.models.permissions import Permissions
from agentstack_server.domain.models.user import UserRole
from agentstack_server.utils.utils import utc_now

logger = logging.getLogger(__name__)


ROLE_PERMISSIONS: dict[UserRole, Permissions] = {
    UserRole.ADMIN: Permissions.all(),
    UserRole.USER: Permissions(
        system_configuration={"read"},
        files={"*"},
        vector_stores={"*"},
        llm={"*"},
        embeddings={"*"},
        a2a_proxy={"*"},
        feedback={"write"},
        providers={"read"},
        variables={"read", "write"},
        model_providers={"read"},
        contexts={"*"},
        context_data={"*"},
        connectors={"*"},
    ),
}
ROLE_PERMISSIONS[UserRole.DEVELOPER] = ROLE_PERMISSIONS[UserRole.USER] | Permissions(
    providers={"read", "write"},
    feedback={"read", "write"},
    provider_builds={"read", "write"},
    provider_variables={"read", "write"},
)

"""
global entities:
    - model_providers
    - system_configuration
    - mcp_providers
    - mcp_tools
private entities (scoped to user):
    - files
    - vector_stores
    - variables
    - contexts
    - context_data
    - feedback
semi-private entities:
    - providers
        - any user list and show detail about any provider
        - developers can create/delete and manage only their own providers
        - admins can create/delete and manage any provider
    - provider_builds
        - any user list and show detail about any build
        - developers can create/delete and manage only their own builds
        - admins can create/delete and manage any build
"""


class ParsedToken(BaseModel):
    global_permissions: Permissions
    context_permissions: Permissions
    context_id: UUID
    user_id: UUID
    iat: int
    raw: dict[str, Any]


def issue_internal_jwt(
    user_id: UUID,
    context_id: UUID,
    global_permissions: Permissions,
    context_permissions: Permissions,
    configuration: Configuration,
    audience: list[str] | None = None,
    expires_at: AwareDatetime | None = None,
) -> tuple[str, AwareDatetime]:
    assert configuration.auth.jwt_private_key
    secret_key = configuration.auth.jwt_private_key.get_secret_value()
    now = utc_now()
    if expires_at is None:
        expires_at = now + timedelta(minutes=20)
    header = {"alg": "RS256"}

    payload = {
        "context_id": str(context_id),
        "sub": str(user_id),
        "exp": expires_at,
        "iat": now,
        "iss": "agentstack-server",
        "aud": [*(audience or []), "agentstack-server"],
        "resource": [f"context:{context_id}"],
        "scope": {
            "global": global_permissions.model_dump(mode="json"),
            "context": context_permissions.model_dump(mode="json"),
        },
    }
    return jwt.encode(header, payload, key=secret_key).decode("utf-8"), expires_at


def verify_internal_jwt(token: str, configuration: Configuration) -> ParsedToken:
    assert configuration.auth.jwt_public_key
    public_key = configuration.auth.jwt_public_key.get_secret_value()
    claims: JWTClaims = jwt.decode(
        token,
        key=public_key,
        claims_options={
            "sub": {"essential": True},
            "exp": {"essential": True},
            "iss": {"essential": True, "value": "agentstack-server"},
            "aud": {"essential": True, "value": "agentstack-server"},
        },
    )
    claims.validate()
    context_id = UUID(claims["resource"][0].replace("context:", ""))
    return ParsedToken(
        global_permissions=Permissions.model_validate(claims["scope"]["global"]),
        context_permissions=Permissions.model_validate(claims["scope"]["context"]),
        context_id=context_id,
        user_id=UUID(claims["sub"]),
        iat=claims["iat"],
        raw=claims,
    )


def exchange_internal_jwt(
    token: str, configuration: Configuration, audience: list[str] | None = None
) -> tuple[str, AwareDatetime]:
    parsed_token = verify_internal_jwt(token, configuration)
    expires_at = datetime.fromtimestamp(parsed_token.raw["exp"], UTC)
    return issue_internal_jwt(
        user_id=parsed_token.user_id,
        context_id=parsed_token.context_id,
        global_permissions=parsed_token.global_permissions,
        context_permissions=parsed_token.context_permissions,
        configuration=configuration,
        audience=audience,
        expires_at=expires_at,
    )


@alru_cache(ttl=timedelta(minutes=60).seconds)
async def discover_issuer(provider: OidcProvider) -> AuthorizationServerMetadata | OpenIDProviderMetadata:
    try:
        async with httpx.AsyncClient(headers={"Accept": "application/json"}) as client:
            try:
                url = oauth_get_well_known_url(str(provider.issuer), external=True)
                response = await client.get(url)
                response.raise_for_status()
                metadata = AuthorizationServerMetadata(response.json())
                metadata.validate_issuer()
                metadata.validate_jwks_uri()
                metadata.validate_introspection_endpoint()
            except Exception as e:
                # Fallback to OIDC 1.0
                try:
                    url = oidc_get_well_known_url(str(provider.issuer), external=True)
                    response = await client.get(url)
                    response.raise_for_status()
                    metadata = OpenIDProviderMetadata(response.json())
                    metadata.validate_issuer()
                    metadata.validate_jwks_uri()
                    metadata.validate_introspection_endpoint()
                except Exception as fallback_e:
                    logger.warning(f"Issuer discovery fallback failed for provider {provider.issuer}: {fallback_e}")
                    raise fallback_e from e
        return metadata
    except Exception as e:
        logger.warning(f"Issuer discovery failed for provider {provider.issuer}: {e}")
        raise IssuerDiscoveryError(f"Issuer discovery failed for provider {provider.issuer}: {e}") from e


@alru_cache(ttl=timedelta(minutes=15).seconds)
async def discover_jwks(provider: OidcProvider) -> KeySet:
    issuer = await discover_issuer(provider)
    jwks_uri = issuer.get("jwks_uri")
    if not isinstance(jwks_uri, str):
        raise JWKSDiscoveryError(f"Provider {provider.issuer} does not support JWKS discovery")

    try:
        async with httpx.AsyncClient(headers={"Accept": "application/json"}) as client:
            response = await client.get(jwks_uri)
            response.raise_for_status()
            return JsonWebKey.import_key_set(response.json())
    except Exception as e:
        logger.warning(f"JWKS discovery failed for provider {provider.issuer}: {e}")
        raise JWKSDiscoveryError(f"JWKS discovery failed for provider {provider.issuer}: {e}") from e


def extract_oauth_token(
    header_token: str | HTTPAuthorizationCredentials,
) -> str:
    if isinstance(header_token, HTTPAuthorizationCredentials):
        return header_token.credentials

    try:
        scheme, credentials = header_token.split()
        if scheme.lower() == "bearer":
            return credentials
        raise Exception("Unsupported auth scheme - Bearer is only valid scheme")
    except ValueError as err:
        logger.warning("Invalid Authorization header format")
        raise Exception("Invalid Authorization header format") from err


@alru_cache(ttl=timedelta(seconds=5).seconds)
async def validate_jwt(token: str, *, provider: OidcProvider, aud: Iterable[str]) -> JWTClaims | Exception:
    keyset = await discover_jwks(provider)
    try:
        claims = jwt.decode(
            token,
            key=keyset,
            claims_options={
                "sub": {"essential": True},
                "exp": {"essential": True},
                "iss": {"essential": True, "values": {str(provider.external_issuer), str(provider.issuer)}},
                "aud": {"essential": True, "values": aud},
            },
        )
        claims.validate()
        return claims
    except Exception as e:
        return e  # Cache exception response


@alru_cache(ttl=timedelta(seconds=15).seconds)
async def introspect_token(token: str, *, provider: OidcProvider, aud: Iterable[str]) -> JWTClaims | Exception:
    """Call OAuth2 introspect endpoint to validate opaque token"""

    async with httpx.AsyncClient() as client:
        issuer = await discover_issuer(provider)
        introspection_endpoint = issuer.get("introspection_endpoint")
        if not isinstance(introspection_endpoint, str):
            raise IntrospectionDiscoveryError(f"Provider {provider.issuer} does not support introspection discovery")
        try:
            resp = await client.post(
                introspection_endpoint,
                auth=(provider.client_id, provider.client_secret.get_secret_value()),
                data={"token": token},
            )
            resp.raise_for_status()
            token = resp.json()
            try:
                IntrospectTokenValidator().validate_token(token, None, None)
                claims = JWTClaims(
                    token,
                    header={},
                    options={"iss": {"value": str(provider.issuer)}, "aud": {"values": aud}},
                )
                claims.validate()
                return claims
            except Exception as e:
                return e  # Cache exception response
        except Exception as e:
            logger.warning(f"Introspection failed for provider {provider.issuer}: {e}")
            raise IntrospectionDiscoveryError(
                f"Provider {provider.issuer} does not support introspection discovery"
            ) from e


async def validate_oauth_access_token(
    configuration: Configuration, token: str, aud: Iterable[str]
) -> tuple[JWTClaims | None, OidcProvider]:
    provider = configuration.auth.oidc.provider

    try:
        claims_or_exc = await validate_jwt(token, provider=provider, aud=frozenset(aud))
        if isinstance(claims_or_exc, Exception):
            raise claims_or_exc
        return claims_or_exc, provider
    except (
        DecodeError,  # Not a JWT
        KeyMismatchError,  # None of the keys match for the issuer
        JWKSDiscoveryError,  # JWKS validation is not working
    ):
        pass

    claims_or_exc = await introspect_token(token, provider=provider, aud=frozenset(aud))
    if isinstance(claims_or_exc, Exception):
        raise claims_or_exc
    return claims_or_exc, provider


@alru_cache(ttl=timedelta(seconds=15).seconds)
async def get_user_info(token: str, *, provider: OidcProvider) -> dict:
    """Get user info from OIDC userinfo endpoint using access token"""

    issuer = await discover_issuer(provider)
    userinfo_endpoint = issuer.get("userinfo_endpoint")
    if not isinstance(userinfo_endpoint, str):
        raise UserInfoDiscoveryError(f"Provider {provider.issuer} does not support userinfo discovery")

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(userinfo_endpoint, headers={"Authorization": f"Bearer {token}"})
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.warning(f"UserInfo discovery failed for provider {provider.issuer}: {e}")
        raise UserInfoDiscoveryError(f"UserInfo discovery failed for provider {provider.issuer}: {e}") from e


async def validate_basic_auth(username: str, password: str, configuration: Configuration) -> str:
    """
    Validate basic auth credentials against the OIDC provider using the Resource Owner Password Credentials Grant.
    """
    provider = configuration.auth.oidc.provider
    issuer = await discover_issuer(provider)
    token_endpoint = issuer.get("token_endpoint")
    if not isinstance(token_endpoint, str):
        raise IssuerDiscoveryError(f"Provider {provider.issuer} does not support token endpoint discovery")

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                token_endpoint,
                data={
                    "grant_type": "password",
                    "username": username,
                    "password": password,
                    "client_id": provider.client_id,
                    "client_secret": provider.client_secret.get_secret_value(),
                    "scope": "openid email profile",  # Request standard scopes
                },
            )
            access_token: str = cast(str, resp.raise_for_status().json()["access_token"])
            return access_token
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                # Invalid credentials
                raise ValueError("Invalid credentials") from e
            logger.warning(f"Basic auth validation failed for user {username}: {e}")
            raise ValueError(f"Basic auth validation failed: {e}") from e
        except Exception as e:
            logger.warning(f"Basic auth validation unexpected error for user {username}: {e}")
            raise ValueError(f"Basic auth validation failed: {e}") from e
