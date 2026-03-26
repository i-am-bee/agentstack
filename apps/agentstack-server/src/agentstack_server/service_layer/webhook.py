# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import asyncio
import fnmatch
import logging
from uuid import UUID

import httpx
from kink import di

from agentstack_server.configuration import Configuration, WebhookEndpoint
from agentstack_server.utils.utils import utc_now

logger = logging.getLogger(__name__)

# Strong references keep fire-and-forget tasks alive until completion.
# See: https://docs.python.org/3/library/asyncio-task.html#creating-tasks
_background_tasks: set[asyncio.Task] = set()


def _matches_event(patterns: list[str], event_type: str) -> bool:
    """Check if event_type matches any of the patterns.

    Supports: "*" (all events), "provider.*" (wildcard), "provider.created" (exact).
    """
    return any(fnmatch.fnmatch(event_type, pattern) for pattern in patterns)


async def _deliver(
    endpoint: WebhookEndpoint,
    event_type: str,
    resource_type: str,
    resource_id: str,
    resource_url: str,
    user_id: str | None,
) -> None:
    """POST webhook payload to endpoint. Logs errors, never raises."""
    payload = {
        "event": event_type,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "resource_url": resource_url,
        "user_id": user_id,
        "timestamp": utc_now().isoformat(),
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                str(endpoint.url),
                json=payload,
                headers={
                    "Authorization": f"Bearer {endpoint.secret.get_secret_value()}",
                    "X-Webhook-Event": event_type,
                },
            )
    except BaseException:
        logger.warning("Failed to deliver webhook to %s for event %s", endpoint.url, event_type, exc_info=True)


def dispatch_webhook_event(
    *,
    event_type: str,
    resource_type: str,
    resource_id: UUID,
    resource_url: str,
    user_id: UUID | None = None,
) -> None:
    """Fire-and-forget webhook notifications to all matching configured endpoints."""
    configuration = di[Configuration]
    endpoints = configuration.webhook.endpoints
    if not endpoints:
        return

    resource_id_str = str(resource_id)
    user_id_str = str(user_id) if user_id else None

    for endpoint in endpoints:
        if _matches_event(endpoint.events, event_type):
            task = asyncio.create_task(
                _deliver(
                    endpoint=endpoint,
                    event_type=event_type,
                    resource_type=resource_type,
                    resource_id=resource_id_str,
                    resource_url=resource_url,
                    user_id=user_id_str,
                )
            )
            _background_tasks.add(task)
            task.add_done_callback(_background_tasks.discard)
