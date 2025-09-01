# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import json
import logging
from datetime import timedelta
from typing import Any
from uuid import UUID

import httpx
import jwt
import requests
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import AwareDatetime, BaseModel

from beeai_server.configuration import Configuration
from beeai_server.domain.models.permissions import Permissions
from beeai_server.domain.models.user import UserRole
from beeai_server.utils.utils import utc_now

logger = logging.getLogger(__name__)


ROLE_PERMISSIONS: dict[UserRole, Permissions] = {
    UserRole.admin: Permissions.all(),
    UserRole.user: Permissions(
        files={"*"},
        vector_stores={"*"},
        llm={"*"},
        embeddings={"*"},
        a2a_proxy={"*"},
        feedback={"write"},
        providers={"read"},
        contexts={"*"},
        mcp_providers={"read"},
        mcp_tools={"read"},
        mcp_proxy={"*"},
    ),
}
ROLE_PERMISSIONS[UserRole.developer] = ROLE_PERMISSIONS[UserRole.user] | Permissions(
    providers={"read", "write"},  # TODO provider ownership
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
    return jwt.encode(payload, secret_key, algorithm="HS256"), expires_at


def verify_internal_jwt(token: str, configuration: Configuration) -> ParsedToken:
    assert configuration.auth.jwt_secret_key
    secret_key = configuration.auth.jwt_secret_key.get_secret_value()
    payload = jwt.decode(token, secret_key, algorithms=["HS256"], audience="beeai-server", issuer="beeai-server")
    context_id = UUID(payload["resource"][0].replace("context:", ""))
    return ParsedToken(
        global_permissions=Permissions.model_validate(payload["scope"]["global"]),
        context_permissions=Permissions.model_validate(payload["scope"]["context"]),
        context_id=context_id,
        user_id=UUID(payload["sub"]),
        raw=payload,
    )


type JWKS_DICT = dict | None


def setup_jwks(config: Configuration) -> JWKS_DICT:
    if config.auth.oidc.disable_oidc:
        return None

    jwks_dict_by_issuer = {}
    for provider in config.auth.oidc.providers:
        issuer = provider.issuer
        if not issuer:
            logger.warning(f"Skipping provider with missing issuer: {provider.name}")
            continue
        try:
            response = requests.get(f"{issuer}/jwks")
            response.raise_for_status()
            jwks_dict = response.json()
            jwks_dict_by_issuer[issuer] = jwks_dict
            logger.debug(f"Fetched JWKS for issuer {issuer} from {issuer}/jwks")
        except Exception as e:
            logger.error(f"Failed to fetch JWKS from {issuer}/jwks : {e}")

    return jwks_dict_by_issuer


def extract_oauth_token(
    header_token: str | HTTPAuthorizationCredentials,
    cookie_token: str | None,
) -> str | None:
    if isinstance(header_token, HTTPAuthorizationCredentials):
        return header_token.credentials

    if header_token:
        try:
            scheme, credentials = header_token.split()
            if scheme.lower() == "bearer":
                return credentials
            raise Exception("Unsupported auth scheme - Bearer is only valid scheme")
        except ValueError as err:
            logger.warning("Invalid Authorization header format")
            raise Exception("Invalid Authorization header format") from err

    # Fall back to cookie if no token in header
    return cookie_token


async def introspect_token(token: str, configuration: Configuration) -> tuple[dict | None, str | None]:
    """Call OAuth2 introspect endpoint to validate opaque token"""
    async with httpx.AsyncClient() as client:
        for provider in configuration.auth.oidc.providers:
            try:
                resp = await client.post(
                    f"{provider.issuer}/introspect",
                    auth=(provider.client_id, provider.client_secret.get_secret_value()),
                    data={"token": token},
                )
                resp.raise_for_status()
                token_info = resp.json()
                if token_info.get("active"):
                    logger.debug(f"Token validated by provider: {provider.issuer}/introspect")
                    return token_info, provider.issuer
                else:
                    logger.debug(f"Token inactive for provider: {provider.issuer}/introspect")
            except Exception as e:
                logger.warning(f"Introspection failed for {provider.issuer}/introspect: {e}")
        logger.error("Token introspection failed for all providers")
        return None, None


async def decode_oauth_jwt_or_introspect(
    token: str, jwks_dict: dict[str, dict] | None = None, aud: str | None = None, configuration=Configuration
) -> tuple[dict, str] | None:
    if jwks_dict:
        for issuer, jwks in jwks_dict.items():
            # Decode JWT using keys from JWKS
            for pub_key in jwks.get("keys", []):
                try:
                    obj_key = jwt.PyJWK(pub_key)
                    # explicitly only check exp and iat, nbf (not before time) is not included in w3id
                    claims = jwt.decode(
                        token, obj_key, algorithms=["RS256"], options=None, verify=True, audience=aud, issuer=issuer
                    )
                    logger.debug("Verified token claims: %s", json.dumps(claims))
                    return claims, issuer
                except jwt.ExpiredSignatureError as err:
                    logger.error("Expired token: %s", err)
                except jwt.InvalidTokenError as err:
                    logger.debug("Token verification failed: %s", err)
                    continue

    logger.info("JWT decoding failed or no JWKS, trying introspection on all providers")
    return await introspect_token(token=token, configuration=configuration)


async def fetch_user_info(token: str, userinfo_endpoint: str) -> dict:
    """Fetch user info from OIDC userinfo endpoint using access token"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(userinfo_endpoint, headers={"Authorization": f"Bearer {token}"})
        if resp.status_code != 200:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Failed to fetch user info")
        return resp.json()
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Userinfo endpoint unreachable: {e}"
        ) from e
