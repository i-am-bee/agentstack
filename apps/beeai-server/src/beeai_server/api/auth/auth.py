# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from datetime import timedelta
from typing import Any
from uuid import UUID

import httpx
from async_lru import alru_cache
from authlib.jose import JWTClaims, jwt
from authlib.jose.errors import DecodeError, KeyMismatchError
from authlib.jose.rfc7517 import KeySet
from authlib.oauth2.rfc8414 import AuthorizationServerMetadata
from authlib.oauth2.rfc8414 import get_well_known_url as oauth_get_well_known_url
from authlib.oidc.discovery import OpenIDProviderMetadata
from authlib.oidc.discovery import get_well_known_url as oidc_get_well_known_url
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import AwareDatetime, BaseModel

from beeai_server.api.auth.errors import (
    IntrospectionDiscoveryError,
    IssuerDiscoveryError,
    JWKSDiscoveryError,
    UserInfoDiscoveryError,
)
from beeai_server.configuration import Configuration, OidcProvider
from beeai_server.domain.models.permissions import Permissions
from beeai_server.domain.models.user import UserRole
from beeai_server.utils.utils import utc_now

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
        model_providers={"read"},
        contexts={"*"},
        context_data={"*"},
        mcp_providers={"read"},
        mcp_tools={"read"},
        mcp_proxy={"*"},
    ),
}
ROLE_PERMISSIONS[UserRole.DEVELOPER] = ROLE_PERMISSIONS[UserRole.USER] | Permissions(
    providers={"read", "write"},  # TODO provider ownership
    provider_variables={"read", "write"},
    mcp_providers={"read", "write"},
)


class ParsedToken(BaseModel):
    global_permissions: Permissions
    context_permissions: Permissions
    context_id: UUID
    user_id: UUID
    raw: dict[str, Any]


def issue_internal_jwt(
    user_id: UUID,
    context_id: UUID,
    global_permissions: Permissions,
    context_permissions: Permissions,
    configuration: Configuration,
) -> tuple[str, AwareDatetime]:
    assert configuration.auth.jwt_secret_key
    secret_key = configuration.auth.jwt_secret_key.get_secret_value()
    now = utc_now()
    expires_at = now + timedelta(minutes=20)
    header = {"alg": "HS256"}
    payload = {
        "context_id": str(context_id),
        "sub": str(user_id),
        "exp": expires_at,
        "iat": now,
        "iss": "beeai-server",
        "aud": "beeai-server",  # the token is for ourselves, noone else should consume it
        "resource": [f"context:{context_id}"],
        "scope": {
            "global": global_permissions.model_dump(mode="json"),
            "context": context_permissions.model_dump(mode="json"),
        },
    }
    return jwt.encode(header, payload, key=secret_key), expires_at


def verify_internal_jwt(token: str, configuration: Configuration) -> ParsedToken:
    assert configuration.auth.jwt_secret_key
    secret_key = configuration.auth.jwt_secret_key.get_secret_value()
    payload = jwt.decode(
        token,
        key=secret_key,
        claims_options={
            "sub": {"essential": True},
            "exp": {"essential": True},
            "iss": {"essential": True, "value": "beeai-server"},
            "aud": {"essential": True, "value": "beeai-server"},
        },
    )
    context_id = UUID(payload["resource"][0].replace("context:", ""))
    return ParsedToken(
        global_permissions=Permissions.model_validate(payload["scope"]["global"]),
        context_permissions=Permissions.model_validate(payload["scope"]["context"]),
        context_id=context_id,
        user_id=UUID(payload["sub"]),
        raw=payload,
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
            except Exception as e:
                # Fallback to OIDC 1.0
                try:
                    url = oidc_get_well_known_url(str(provider.issuer), external=True)
                    response = await client.get(url)
                    response.raise_for_status()
                    metadata = OpenIDProviderMetadata(response.json())
                except Exception:
                    logger.warning(f"Issuer discovery fallback failed for provider {provider.issuer}: {e}")
                    raise e  # noqa: B904
        metadata.validate_issuer()
        metadata.validate_jwks_uri()
        metadata.validate_introspection_endpoint()
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
            return KeySet(response.json())
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


@alru_cache(ttl=timedelta(seconds=15).seconds)
async def introspect_token(token: str, *, provider: OidcProvider) -> None:
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
            token_info = resp.json()
            if token_info.get("active"):
                logger.debug(f"Token validated by provider: {provider.issuer}")
                return
            else:
                logger.debug(f"Token inactive for provider: {provider.issuer}")
        except Exception as e:
            logger.warning(f"Introspection failed for {provider.issuer}: {e}")


async def validate_oauth_access_token(
    configuration: Configuration, token: str, aud: str | None = None
) -> tuple[JWTClaims | None, OidcProvider]:
    exceptions: list[Exception] = []

    for provider in configuration.auth.oidc.providers:
        try:
            keyset = await discover_jwks(provider)
        except Exception as e:
            exceptions.append(e)
            continue

        try:
            claims = jwt.decode(
                token,
                key=keyset,
                claims_options={
                    "sub": {"essential": True},
                    "exp": {"essential": True},
                    "iss": {"essential": True, "value": str(provider.issuer)},
                    "aud": {"essential": True, "value": aud},
                },
            )
            claims.validate()
            return claims, provider
        except DecodeError:
            break  # Not a JWT
        except KeyMismatchError:
            continue  # None of the keys match for the issuer

    for provider in configuration.auth.oidc.providers:
        try:
            await introspect_token(token, provider=provider)
            return None, provider
        except Exception as e:
            exceptions.append(e)
            continue

    raise ExceptionGroup("Token validation failed for all providers", exceptions)


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
