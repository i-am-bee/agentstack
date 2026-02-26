# Copyright 2026 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from datetime import timedelta
from typing import Final, override

import cachetools

from agentstack_server.service_layer.cache import ICache, ICacheFactory, ISerializer

DEFAULT_MAX_SIZE: Final[int] = 1024


class MemoryCache[T](ICache[T]):
    def __init__(self, ttl: timedelta | None = None, max_size: int = DEFAULT_MAX_SIZE):
        self.cache: cachetools.Cache[str, T] = (
            cachetools.TTLCache(maxsize=max_size, ttl=ttl.total_seconds())
            if ttl
            else cachetools.LRUCache(maxsize=max_size)
        )

    @override
    async def add(self, key: str, value: T) -> bool:
        if key in self.cache:
            return False
        self.cache[key] = value
        return True

    @override
    async def clear(self) -> bool:
        self.cache.clear()
        return True

    @override
    async def delete(self, key: str) -> int:
        if key in self.cache:
            del self.cache[key]
            return 1
        return 0

    @override
    async def exists(self, key: str) -> bool:
        return key in self.cache

    @override
    async def get(self, key: str, default: T | None = None) -> T | None:
        return self.cache.get(key, default)

    @override
    async def multi_get(self, keys: list[str], default: T | None = None) -> list[T | None]:
        return [self.cache.get(k, default) for k in keys]

    @override
    async def multi_set(self, pairs: list[tuple[str, T]]) -> bool:
        for k, v in pairs:
            self.cache[k] = v
        return True

    @override
    async def set(self, key: str, value: T) -> bool:
        self.cache[key] = value
        return True

    @override
    async def close(self) -> None:
        pass


class MemoryCacheFactory(ICacheFactory):
    @override
    def create[T](
        self,
        *,
        namespace: str,
        serializer: ISerializer[T],
        ttl: timedelta | None = None,
        timeout_sec: float = 5.0,
    ) -> ICache[T]:
        return MemoryCache[T](ttl=ttl)
