# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-20

import time
from collections.abc import AsyncIterator
from typing import override

import openai.types.chat.chat_completion
import pytest
from fastapi.testclient import TestClient
from kink import Container
from limits import parse_many
from limits.aio.storage import RedisStorage
from openai.types.chat import ChatCompletion
from openai.types.completion_usage import CompletionUsage
from openai.types.create_embedding_response import Usage

from agentstack_server.api.schema.openai import ChatCompletionRequest, EmbeddingsRequest
from agentstack_server.configuration import (
    AuthConfiguration,
    Configuration,
    RateLimitConfiguration,
    RedisConfiguration,
    RoleBasedRateLimitConfiguration,
    RoleRateLimits,
)
from agentstack_server.domain.models.model_provider import Model, ModelProvider
from agentstack_server.domain.repositories.openai_proxy import (
    IOpenAIChatCompletionProxyAdapter,
    IOpenAIEmbeddingProxyAdapter,
    IOpenAIProxy,
)

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
            global_limits=parse_many("3/second"),
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


class MockOpenAIProxyAdapter(IOpenAIChatCompletionProxyAdapter, IOpenAIEmbeddingProxyAdapter):
    def __init__(self, total_tokens: int = 10):
        self.total_tokens = total_tokens

    async def list_models(self, *, api_key: str) -> list[Model]:
        return [
            Model(id="openai:dummy", provider={"capabilities": ["llm", "embedding"]}),
            Model(id="openai:dummy-embedding", provider={"capabilities": ["llm", "embedding"]}),
        ]

    async def create_embedding(
        self, *, request: EmbeddingsRequest, api_key: str
    ) -> openai.types.CreateEmbeddingResponse:
        return openai.types.CreateEmbeddingResponse(
            object="list",
            data=[openai.types.Embedding(embedding=[0.1, 0.2, 0.3], index=0, object="embedding")],
            model=request.model,
            usage=Usage(prompt_tokens=self.total_tokens, total_tokens=self.total_tokens),
        )

    async def create_chat_completion(self, *, request: ChatCompletionRequest, api_key: str) -> ChatCompletion:
        return ChatCompletion(
            id="chatcmpl-123",
            created=int(time.time()),
            model=request.model,
            object="chat.completion",
            choices=[],
            usage=CompletionUsage(completion_tokens=self.total_tokens, prompt_tokens=0, total_tokens=self.total_tokens),
        )

    async def create_chat_completion_stream(
        self, *, request: ChatCompletionRequest, api_key: str
    ) -> AsyncIterator[openai.types.chat.ChatCompletionChunk]:
        yield openai.types.chat.ChatCompletionChunk(
            id="chatcmpl-123",
            created=int(time.time()),
            model=request.model,
            object="chat.completion.chunk",
            choices=[],
        )


class MockOpenAIProxy(IOpenAIProxy):
    def __init__(self, token_usage_per_request: int = 10):
        self.token_usage_per_request = token_usage_per_request

    @override
    async def list_models(self, *, provider: ModelProvider, api_key: str) -> list[Model]:
        return await self.get_chat_completion_proxy(provider=provider).list_models(api_key=api_key)

    @override
    def get_chat_completion_proxy(self, *, provider: ModelProvider) -> IOpenAIChatCompletionProxyAdapter:
        return MockOpenAIProxyAdapter(total_tokens=self.token_usage_per_request)

    @override
    def get_embedding_proxy(self, *, provider: ModelProvider) -> IOpenAIEmbeddingProxyAdapter:
        return MockOpenAIProxyAdapter(total_tokens=self.token_usage_per_request)


@pytest.fixture
def token_rate_limit_config(redis_config) -> Container:
    container = Container()
    # Limit: 20 tokens per minute
    rate_limits = RoleRateLimits(
        openai_chat_completion_requests="5/second",
        openai_chat_completion_tokens="70/minute",
        openai_embedding_inputs="10/second",
    )
    container[Configuration] = Configuration(
        rate_limit=RateLimitConfiguration(
            enabled=True,
            role_based_limits=RoleBasedRateLimitConfiguration(
                user=rate_limits,
                developer=rate_limits,
                admin=rate_limits,
            ),
            strategy="fixed-window",
        ),
        redis=redis_config,
        auth=AuthConfiguration(disable_auth=True),
    )
    # Inject MockOpenAIProxy that uses 10 tokens per request
    container[IOpenAIProxy] = MockOpenAIProxy(token_usage_per_request=10)
    return container


@pytest.fixture
async def token_rate_limited_client(
    agentstack_server, token_rate_limit_config, redis_config, clean_up
) -> AsyncIterator[TestClient]:
    with agentstack_server(dependency_overrides=token_rate_limit_config) as client:
        try:
            response = client.post(
                "/api/v1/model_providers",
                json={
                    "name": "dummy-provider",
                    "description": "Dummy provider for testing",
                    "type": "openai",
                    "base_url": "http://dummy",
                    "api_key": "dummy-key",
                },
            )
            assert response.status_code == 201
            yield client
        finally:
            redis = RedisStorage("async+" + redis_config.rate_limit_db_url.get_secret_value())
            await redis.reset()


def test_rate_limit_tokens(token_rate_limited_client: TestClient):
    """Test that rate limiting is enforced based on token usage."""

    data = {"model": "openai:dummy", "messages": [{"role": "user", "content": "Hi"}]}
    # 1. Each request: costs 10 tokens. Limit is 100/minute
    for _ in range(5):
        response = token_rate_limited_client.post("/api/v1/openai/chat/completions", json=data)
        assert response.status_code == 200

    time.sleep(1.1)

    for _ in range(2):
        response = token_rate_limited_client.post("/api/v1/openai/chat/completions", json=data)
        assert response.status_code == 200

    response = token_rate_limited_client.post("/api/v1/openai/chat/completions", json=data)
    assert response.status_code == 429
    assert response.json()["error"]["type"] == "rate_limit_exceeded"


def test_rate_limit_rps(token_rate_limited_client: TestClient):
    """Test that rate limiting is enforced based on requests per second."""
    # Limit is 5/second.
    data = {"model": "openai:dummy", "messages": [{"role": "user", "content": "Hi"}]}
    # 1. First 5 requests should succeed
    for _ in range(5):
        response = token_rate_limited_client.post("/api/v1/openai/chat/completions", json=data)
        assert response.status_code == 200

    # 2. Sixth request should fail
    response = token_rate_limited_client.post("/api/v1/openai/chat/completions", json=data)
    assert response.status_code == 429
    assert response.json()["error"]["type"] == "rate_limit_exceeded"


def test_rate_limit_embeddings(token_rate_limited_client: TestClient):
    """Test that rate limiting is enforced based on embedding items."""
    # Limit is 10/second (items).
    # 1. First request with 5 items.
    response = token_rate_limited_client.post(
        "/api/v1/openai/embeddings",
        json={"model": "openai:dummy-embedding", "input": ["1", "2", "3", "4", "5"]},
    )
    assert response.status_code == 200

    # 2. Second request with 5 items.
    response = token_rate_limited_client.post(
        "/api/v1/openai/embeddings",
        json={"model": "openai:dummy-embedding", "input": ["6", "7", "8", "9", "10"]},
    )
    assert response.status_code == 200

    # 3. Third request. Limit is used up (10 items total).
    response = token_rate_limited_client.post(
        "/api/v1/openai/embeddings",
        json={"model": "openai:dummy-embedding", "input": ["11"]},
    )
    assert response.status_code == 429
    assert response.json()["error"]["type"] == "rate_limit_exceeded"
