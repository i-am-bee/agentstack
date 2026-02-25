# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from contextlib import asynccontextmanager
from enum import StrEnum
from typing import Final, cast

from limits import RateLimitItem
from limits.aio.storage import Storage
from limits.aio.strategies import STRATEGIES, RateLimiter

from agentstack_server.configuration import Configuration, RoleRateLimits
from agentstack_server.domain.models.user import User, UserRole
from agentstack_server.exceptions import RateLimitExceededError


class RateLimit(StrEnum):
    assert RoleRateLimits.openai_chat_completion_tokens_parsed.attrname
    assert RoleRateLimits.openai_chat_completion_requests_parsed.attrname
    assert RoleRateLimits.openai_embedding_inputs_parsed.attrname

    OPENAI_CHAT_COMPLETION_TOKENS = RoleRateLimits.openai_chat_completion_tokens_parsed.attrname
    OPENAI_CHAT_COMPLETION_REQUESTS = RoleRateLimits.openai_chat_completion_requests_parsed.attrname
    OPENAI_EMBEDDING_ITEMS = RoleRateLimits.openai_embedding_inputs_parsed.attrname


class UserRateLimiter:
    def __init__(self, user: User, configuration: Configuration, storage: Storage):
        self._enabled: bool = configuration.rate_limit.enabled
        self._user: Final[User] = user
        self._limiter: Final[RateLimiter] = STRATEGIES[configuration.rate_limit.strategy](storage=storage)
        self._role_limits: Final[dict[UserRole, RoleRateLimits]] = {
            UserRole.USER: configuration.rate_limit.role_based_limits.user,
            UserRole.DEVELOPER: configuration.rate_limit.role_based_limits.developer,
            UserRole.ADMIN: configuration.rate_limit.role_based_limits.admin,
        }
        self._key: Final[str] = str(user.id)

    def _get_limits(self, limit: RateLimit) -> list[RateLimitItem]:
        if not self._enabled:
            return []
        return cast(list[RateLimitItem], getattr(self._role_limits[self._user.role], RateLimit(limit).value))

    async def hit(self, limit: RateLimit, cost: int = 1) -> None:
        for configured_limit in self._get_limits(limit):
            if not await self._limiter.hit(configured_limit, self._key, cost=cost):
                reset_time, remaining = await self._limiter.get_window_stats(configured_limit, self._key)
                amount = configured_limit.amount
                raise RateLimitExceededError(key=self._key, amount=amount, remaining=remaining, reset_time=reset_time)

    async def test(self, limit: RateLimit, cost: int = 1) -> None:
        for configured_limit in self._get_limits(limit):
            if not await self._limiter.test(configured_limit, self._key, cost=cost):
                reset_time, remaining = await self._limiter.get_window_stats(configured_limit, self._key)
                amount = configured_limit.amount
                raise RateLimitExceededError(key=self._key, amount=amount, remaining=remaining, reset_time=reset_time)

    @asynccontextmanager
    async def limit(self, limit: RateLimit, cost: int = 1):
        if self._enabled:
            await self.hit(limit, cost)
        yield
