# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-20

import time
from collections.abc import AsyncIterator

import pytest
from fastapi.testclient import TestClient
from kink import Container
from limits import parse_many
from limits.aio.storage import RedisStorage

from agentstack_server.configuration import AuthConfiguration, Configuration, RateLimitConfiguration, RedisConfiguration

pytestmark = pytest.mark.integration


@pytest.fixture
def redis_config():
    return RedisConfiguration(enabled=True)


@pytest.fixture
def dependency_overrides_with_rate_limit(redis_config) -> Container:
    """Create a rate limit configuration with low limits for testing."""
    container = Container()
    container[Configuration] = Configuration(
        rate_limit=RateLimitConfiguration(
            enabled=True,
            limits=parse_many("3/second"),
            strategy="fixed-window",
        ),
        redis=redis_config,
        auth=AuthConfiguration(disable_auth=True),
    )
    return container


@pytest.fixture
async def rate_limited_server_client(
    agentstack_server, dependency_overrides_with_rate_limit, redis_config
) -> AsyncIterator[TestClient]:
    with agentstack_server(dependency_overrides=dependency_overrides_with_rate_limit) as client:
        try:
            yield client
        finally:
            redis = RedisStorage("async+" + redis_config.rate_limit_db_url.get_secret_value())
            await redis.reset()


def test_rate_limit_enforced(rate_limited_server_client: TestClient):
    """Test that rate limiting is properly enforced after exceeding configured limits."""

    # First few requests should succeed
    for i in range(3):
        response = rate_limited_server_client.get("/api/v1/contexts")
        assert response.status_code == 200, f"Request {i + 1} should succeed"

        # Verify rate limit headers are present
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        assert "Retry-After" in response.headers

    # Next request should be rate limited
    response = rate_limited_server_client.get("/api/v1/contexts")
    assert response.status_code == 429, "Fourth request should be rate limited"

    # Verify response body
    body = response.json()
    assert body["error"] == "rate_limit_exceeded"
    assert "Rate limit exceeded" in body["detail"]

    # Verify headers on rate-limited response
    assert response.headers["X-RateLimit-Remaining"] == "0"

    # Wait for the rate limit to reset (1 second for "3/second")
    time.sleep(1.1)

    # After reset, a new request should succeed
    response = rate_limited_server_client.get("/api/v1/contexts")
    assert response.status_code == 200, "Request after reset should succeed"
    assert "X-RateLimit-Remaining" in response.headers
    assert int(response.headers["X-RateLimit-Remaining"]) == 2


def test_rate_limit_headers_present_when_enabled(rate_limited_server_client: TestClient):
    """Test that rate limit headers are present when rate limiting is enabled."""

    response = rate_limited_server_client.get("/api/v1/contexts")
    assert response.status_code == 200

    # Check all expected headers
    assert "X-RateLimit-Limit" in response.headers
    assert response.headers["X-RateLimit-Limit"] == "3"

    assert "X-RateLimit-Remaining" in response.headers
    remaining = int(response.headers["X-RateLimit-Remaining"])
    assert remaining == 2  # After first request, 2 remaining

    assert "X-RateLimit-Reset" in response.headers
    assert "Retry-After" in response.headers


def test_rate_limit_different_auth_keys(rate_limited_server_client: TestClient):
    """Test that different auth keys have separate rate limits."""

    # Exhaust rate limit for one IP/key
    for _ in range(3):
        response = rate_limited_server_client.get("/api/v1/contexts")
        assert response.status_code == 200

    # This request should be rate limited
    response = rate_limited_server_client.get("/api/v1/contexts")
    assert response.status_code == 429

    # Request with different auth should have its own limit
    response = rate_limited_server_client.get(
        "/api/v1/contexts",
        headers={"Authorization": "Bearer different-token"},
    )
    assert response.status_code == 200, "Different auth key should have separate rate limit"
