# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import hashlib
import logging
import time
from typing import Final, override

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from limits import RateLimitItem
from limits.aio.storage import Storage
from limits.aio.strategies import STRATEGIES, RateLimiter
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from agentstack_server.configuration import RateLimitConfiguration

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware that uses the limits library.

    Supports both Redis and in-memory storage backends.
    Rate limit keys are generated based on authentication type:
    - Bearer tokens (OAuth/JWT): hashes the token
    - Basic auth: hashes the credentials
    - No auth: uses client IP address
    """

    def __init__(
        self,
        app: ASGIApp,
        limiter_storage: Storage,
        configuration: RateLimitConfiguration,
    ):
        super().__init__(app)
        self.enabled: Final[bool] = configuration.enabled
        self.limits: Final[list[RateLimitItem]] = sorted(configuration.limits_parsed)
        self.limiter: Final[RateLimiter] = STRATEGIES[configuration.strategy](limiter_storage)

        logger.info(
            "Rate limiting initialized\n:"
            + f"  Storage class: {type(limiter_storage).__name__}\n"
            + f"  Strategy class: {type(self.limiter).__name__}\n"
            + f"  Limits: {[str(limit) for limit in self.limits]}"
        )

    def _hash_secret(self, secret: str) -> str:
        return hashlib.sha256(secret.encode()).hexdigest()

    def _extract_auth_key(self, request: Request) -> str:
        """
        Extract authentication key from request for rate limiting.

        Priority:
        1. Bearer token (OAuth/JWT or internal JWT)
        2. Basic auth credentials (hashed)
        3. Client IP address
        """
        # Check for Bearer token
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            return f"bearer:{self._hash_secret(token)}"

        # Check for Basic auth
        if auth_header.startswith("Basic "):
            credentials = auth_header[6:]  # Remove "Basic " prefix
            return f"basic:{self._hash_secret(credentials)}"

        # Fallback to client IP
        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"

    @override
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process request with rate limiting."""
        if not self.enabled or not self.limits or request.url.path == "/healthcheck":
            return await call_next(request)

        # Generate rate limit key
        rate_limit_key = self._extract_auth_key(request)

        response: Response

        # Check all configured limits
        header_limit = self.limits[0]  # return the first limit which should be the shortest time period

        for limit in self.limits:
            if not await self.limiter.hit(limit, rate_limit_key):
                logger.warning(
                    f"Rate limit exceeded for key '{rate_limit_key[:20]}...' "
                    + f"on {request.method} {request.url.path} (limit: {limit})"
                )

                header_limit = limit
                response = JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"error": "rate_limit_exceeded", "detail": f"Rate limit exceeded: {limit}"},
                )
                break
        else:
            response = await call_next(request)

        reset_time, remaining = await self.limiter.get_window_stats(header_limit, rate_limit_key)

        if existing_retry_after_header := response.headers.get("Retry-After"):
            try:
                retry_after = int(existing_retry_after_header)
                retry_after_timestamp = time.time() + retry_after
                reset_time = max(reset_time, retry_after_timestamp)
            except ValueError:
                logger.warning(f"Invalid Retry-After header value: {existing_retry_after_header}")

        response.headers["X-RateLimit-Limit"] = str(header_limit.amount)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        response.headers["Retry-After"] = str(int(reset_time - time.time()))

        return response
