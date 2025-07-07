# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import functools
import logging
from collections.abc import AsyncIterable
from contextlib import AsyncExitStack
from datetime import timedelta
from typing import NamedTuple
from uuid import UUID

import httpx
from kink import inject
from structlog.contextvars import bind_contextvars, unbind_contextvars

from beeai_server.configuration import Configuration
from beeai_server.domain.models.provider import ProviderDeploymentState
from beeai_server.service_layer.deployment_manager import IProviderDeploymentManager
from beeai_server.service_layer.services.users import UserService
from beeai_server.service_layer.unit_of_work import IUnitOfWorkFactory

logger = logging.getLogger(__name__)


class A2AServerResponse(NamedTuple):
    content: bytes | None
    stream: AsyncIterable | None
    status_code: int
    headers: dict[str, str] | None
    media_type: str


class ProxyClient:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    @functools.wraps(httpx.AsyncClient.stream)
    async def send_request(self, **kwargs) -> A2AServerResponse:
        exit_stack = AsyncExitStack()
        try:
            client = await exit_stack.enter_async_context(self._client)
            resp: httpx.Response = await exit_stack.enter_async_context(client.stream(**kwargs))
            is_stream = resp.headers["content-type"].startswith("text/event-stream")

            async def stream_fn():
                try:
                    async for event in resp.stream:
                        yield event
                finally:
                    await exit_stack.pop_all().aclose()

            common = {
                "status_code": resp.status_code,
                "headers": resp.headers,
                "media_type": resp.headers["content-type"],
            }
            if is_stream:
                return A2AServerResponse(content=None, stream=stream_fn(), **common)
            else:
                try:
                    await resp.aread()
                    return A2AServerResponse(stream=None, content=resp.content, **common)
                finally:
                    await exit_stack.pop_all().aclose()
        except BaseException:
            await exit_stack.pop_all().aclose()
            raise


@inject
class A2AProxyService:
    STARTUP_TIMEOUT = timedelta(minutes=5)

    def __init__(
        self,
        provider_deployment_manager: IProviderDeploymentManager,
        uow: IUnitOfWorkFactory,
        user_service: UserService,
        configuration: Configuration,
    ):
        self._deploy_manager = provider_deployment_manager
        self._uow = uow
        self._user_service = user_service
        self._config = configuration

    async def get_proxy_client(self, *, provider_id: UUID) -> ProxyClient:
        try:
            bind_contextvars(provider=provider_id)

            async with self._uow() as uow:
                provider = await uow.providers.get(provider_id=provider_id)
                await uow.providers.update_last_accessed(provider_id=provider_id)
                await uow.commit()

            if not provider.managed:
                return ProxyClient(httpx.AsyncClient(base_url=str(provider.source.root), timeout=None))

            provider_url = await self._deploy_manager.get_provider_url(provider_id=provider.id)
            [state] = await self._deploy_manager.state(provider_ids=[provider.id])
            should_wait = False
            match state:
                case ProviderDeploymentState.error:
                    raise RuntimeError("Provider is in an error state")
                case (
                    ProviderDeploymentState.missing
                    | ProviderDeploymentState.running
                    | ProviderDeploymentState.starting
                    | ProviderDeploymentState.ready
                ):
                    async with self._uow() as uow:
                        env = await uow.env.get_all()
                    modified = await self._deploy_manager.create_or_replace(provider=provider, env=env)
                    should_wait = modified or state != ProviderDeploymentState.running
                case _:
                    raise ValueError(f"Unknown provider state: {state}")
            if should_wait:
                logger.info("Waiting for provider to start up...")
                await self._deploy_manager.wait_for_startup(provider_id=provider.id, timeout=self.STARTUP_TIMEOUT)
                logger.info("Provider is ready...")
            return ProxyClient(httpx.AsyncClient(base_url=str(provider_url), timeout=None))
        finally:
            unbind_contextvars("provider")
