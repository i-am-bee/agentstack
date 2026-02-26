# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import httpx
import pytest
from sqlalchemy import text

pytestmark = pytest.mark.e2e


@pytest.fixture
def api_base_url(test_configuration):
    return test_configuration.server_url


async def test_basic_auth_success(api_base_url, test_user, subtests):
    """
    Verify that a user created in Keycloak can authenticate using Basic Auth
    and access a protected endpoint.
    """
    url = f"{api_base_url}/api/v1/users/me"
    with subtests.test("valid credentials"):
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, auth=test_user)
            assert resp.status_code == 200, f"Failed to auth: {resp.text}"
            data = resp.json()
            assert data["email"] == f"{test_user[0]}@beeai.dev"
    with subtests.test("invalid credentials"):
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, auth=("nonexistent_user_123", "wrongpassword"))
            assert resp.status_code == 401


async def test_oidc_bearer_auth(api_base_url, test_user, test_configuration, subtests):
    """
    Verify that a user created in Keycloak can authenticate using Bearer Auth
    and access a protected endpoint.
    """
    url = f"{api_base_url}/api/v1/users/me"
    with subtests.test("valid credentials"):
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{test_configuration.keycloak_url}/realms/agentstack/protocol/openid-connect/token",
                data={
                    "grant_type": "password",
                    "username": test_user[0],
                    "password": test_user[1],
                    "client_id": "agentstack-server",
                    "client_secret": "agentstack-server-secret",
                    "scope": "openid email profile",  # Request standard scopes
                },
            )
            access_token = resp.raise_for_status().json()["access_token"]

            resp = await client.get(url, headers={"Authorization": f"Bearer {access_token}"})
            data = resp.json()
            assert resp.status_code == 200
            assert data["email"] == f"{test_user[0]}@beeai.dev"

    with subtests.test("invalid credentials"):
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers={"Authorization": "Bearer malformed-token"})
            assert resp.status_code == 401


async def test_user_sync_on_login(api_base_url, test_second_user, db_transaction):
    """
    Verify that a user is created in the local database upon successful Basic Auth login.
    """
    # Note: test_second_user creates a fresh user in Keycloak, so likely not in DB yet unless synced by some background process (unlikely for basic auth)

    # Login to trigger sync
    url = f"{api_base_url}/api/v1/users/me"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, auth=test_second_user)
        assert resp.status_code == 200

    email = f"{test_second_user[0]}@beeai.dev"
    result = await db_transaction.execute(text("SELECT email FROM users WHERE email = :email"), {"email": email})
    assert result.scalar_one_or_none() == email
