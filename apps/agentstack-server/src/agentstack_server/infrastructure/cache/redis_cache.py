# Copyright 2026 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from datetime import timedelta
from typing import override

import coredis
from coredis.tokens import PureToken

from agentstack_server.service_layer.cache import ICache, ICacheFactory, ISerializer


class RedisCache[T](ICache[T]):
    def __init__(
        self,
        redis: coredis.Redis[str],
        serializer: ISerializer[T],
        namespace: str,
        ttl: timedelta | None = None,
    ):
        self.redis: coredis.Redis[str] = redis
        self.ttl: int | None = int(ttl.total_seconds()) if ttl else None
        self.namespace: str = namespace
        self.serializer: ISerializer[T] = serializer

    def _key(self, key: str) -> str:
        return f"{self.namespace}:{key}"

    def _serialize(self, value: T) -> str:
        return self.serializer.dumps(value)

    def _deserialize(self, value: str) -> T:
        return self.serializer.loads(value)

    @override
    async def add(self, key: str, value: T) -> bool:
        return bool(await self.redis.set(self._key(key), self._serialize(value), condition=PureToken.NX, ex=self.ttl))

    @override
    async def clear(self) -> bool:
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(cursor, match=f"{self.namespace}:*")
            if not keys:
                break
            await self.redis.delete(keys)
        return True

    @override
    async def delete(self, key: str) -> int:
        return await self.redis.delete([self._key(key)])

    @override
    async def exists(self, key: str) -> bool:
        return bool(await self.redis.exists([self._key(key)]))

    @override
    async def get(self, key: str, default: T | None = None) -> T | None:
        val = await self.redis.get(self._key(key))
        if val is None:
            return default
        return self._deserialize(val)

    @override
    async def multi_get(self, keys: list[str], default: T | None = None) -> list[T | None]:
        if not keys:
            return []
        prefixed_keys = tuple(self._key(k) for k in keys)
        values = await self.redis.mget(prefixed_keys)
        return [self._deserialize(v) if v is not None else default for v in values]

    @override
    async def multi_set(self, pairs: list[tuple[str, T]]) -> bool:
        if not pairs:
            return True
        pipeline = await self.redis.pipeline()
        for k, v in pairs:
            await pipeline.set(self._key(k), self._serialize(v), ex=self.ttl)
        await pipeline.execute()
        return True

    @override
    async def set(self, key: str, value: T) -> bool:
        return bool(await self.redis.set(self._key(key), self._serialize(value), ex=self.ttl))

    @override
    async def close(self) -> None:
        pass


class RedisCacheFactory(ICacheFactory):
    def __init__(self, redis_url):
        self.redis_url = redis_url

    def create[T](
        self,
        *,
        namespace: str,
        serializer: ISerializer[T],
        ttl: timedelta | None = None,
        timeout_sec: float = 5.0,
    ) -> ICache[T]:
        redis = coredis.Redis.from_url(
            self.redis_url,
            decode_responses=True,
            stream_timeout=timeout_sec,
            connect_timeout=timeout_sec,
        )
        return RedisCache[T](redis, serializer, namespace, ttl)
