# Copyright 2026 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from datetime import timedelta

import coredis
import pytest

from agentstack_server.configuration import Configuration
from agentstack_server.infrastructure.cache.memory_cache import MemoryCache
from agentstack_server.infrastructure.cache.redis_cache import RedisCache
from agentstack_server.infrastructure.cache.serializers import JsonSerializer

pytestmark = pytest.mark.integration


@pytest.fixture
async def redis_client():
    config = Configuration().redis
    client = coredis.Redis(
        host=config.host,
        port=config.port,
        password=config.password.get_secret_value() if config.password else None,
        db=config.cache_db,
    )
    try:
        yield client
    finally:
        await client.flushdb()


@pytest.fixture(params=("memory_cache", "redis_cache"))
async def cache(request, redis_client):
    if request.param == "memory_cache":
        return MemoryCache()
    else:
        return RedisCache(redis=redis_client, namespace="test", serializer=JsonSerializer(), ttl=timedelta(minutes=1))


async def test_cache_set_get(cache):
    key = "test_key"
    value = "test_value"

    assert await cache.set(key, value)
    assert await cache.get(key) == value


async def test_cache_add_existing(cache):
    key = "existing_key"
    value = "value"

    assert await cache.set(key, value)
    assert await cache.add(key, "new_value") is False
    assert await cache.get(key) == value


async def test_cache_delete(cache):
    key = "delete_key"
    value = "value"

    await cache.set(key, value)
    assert await cache.delete(key)
    assert await cache.get(key) is None


async def test_cache_exists(cache):
    key = "exists_key"
    value = "value"

    assert await cache.exists(key) is False
    await cache.set(key, value)
    assert await cache.exists(key)


async def test_cache_multi_get_set(cache):
    pairs = [("k1", "v1"), ("k2", "v2")]

    assert await cache.multi_set(pairs)
    values = await cache.multi_get(["k1", "k2"])
    assert values == ["v1", "v2"]


async def test_cache_clear(cache):
    await cache.set("k1", "v1")
    await cache.set("k2", "v2")

    assert await cache.clear()
    assert await cache.get("k1") is None
    assert await cache.get("k2") is None
