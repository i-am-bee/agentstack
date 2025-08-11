# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import os

import jwt
import requests
from fastapi.security import HTTPAuthorizationCredentials
from jwt import ExpiredSignatureError, InvalidTokenError, PyJWK

from beeai_server.api.dependencies import ConfigurationDependency
from beeai_server.configuration import get_configuration

logger = logging.getLogger(__name__)

configuration: ConfigurationDependency = get_configuration()


# Initialize JWKS only if OIDC is enabled
if not configuration.oidc.disable_oidc:
    audience = configuration.oidc.client_id
    JWKS_URL = configuration.oidc.jwks_url
    JWKS_FOLDER = "/tmp/jwks"
    JWKS_FILE = os.path.join(JWKS_FOLDER, "pubkeys.json")

    os.makedirs(JWKS_FOLDER, exist_ok=True)

    try:
        response = requests.get(JWKS_URL)
        response.raise_for_status()
        with open(JWKS_FILE, "w") as f:
            json.dump(response.json(), f, indent=2)
        print(f"JWKS downloaded and saved to: {JWKS_FILE}")
    except Exception as e:
        logger.error("Failed to fetch JWKS: %s", e)
        raise

    def get_jwks_dict():
        with open(JWKS_FILE) as key_file:
            return json.load(key_file)

    jwks_dict = get_jwks_dict()
else:
    jwks_dict = None
    audience = None


def extract_token(
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


def decode_jwt_token(token: str, jwks: dict | None = None, aud: str | None = None) -> dict | None:
    jwks = jwks or jwks_dict
    aud = aud or audience
    logger.debug("aud=%s", str(aud))
    logger.debug("audience=%s", str(audience))
    # Decode JWT using keys from JWKS
    for pub_key in jwks.get("keys", []):
        try:
            obj_key = PyJWK(pub_key)
            # explicitly only check exp and iat, nbf (not before time) is not included in w3id
            claims = jwt.decode(token, obj_key, algorithms=["RS256"], options=None, verify=True, audience=aud)
            logger.debug("Verified token claims: %s", json.dumps(claims))
            return claims
        except ExpiredSignatureError as err:
            logger.error("Expired token: %s", err)
        except InvalidTokenError as err:
            logger.debug("Token verification failed: %s", err)
            continue

    logger.info("All JWT verifications failed.")
    return None
