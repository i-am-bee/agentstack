# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import functools
import logging
from collections.abc import AsyncIterable
from contextlib import AsyncExitStack
from datetime import timedelta
from typing import Any, NamedTuple, cast
from uuid import UUID

import httpx
from httpx import AsyncByteStream
from kink import inject
from structlog.contextvars import bind_contextvars, unbind_contextvars

from beeai_server.configuration import Configuration
from beeai_server.domain.models.provider import (
    NetworkProviderLocation,
    ProviderDeploymentState,
)
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
    async def send_request(*args, **kwargs) -> A2AServerResponse:
        self = args[0]  # extract self for type checking
        rest_args: tuple[Any, ...] = args[1:]
        exit_stack = AsyncExitStack()
        try:
            client = await exit_stack.enter_async_context(self._client)
            resp: httpx.Response = await exit_stack.enter_async_context(client.stream(*rest_args, **kwargs))

            try:
                content_type = resp.headers["content-type"]
                is_stream = content_type.startswith("text/event-stream")
            except KeyError:
                content_type = None
                is_stream = False

            async def stream_fn():
                try:
                    async for event in cast(AsyncByteStream, resp.stream):
                        yield event
                finally:
                    await exit_stack.pop_all().aclose()

            common = {
                "status_code": resp.status_code,
                "headers": resp.headers,
                "media_type": content_type,
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
                if not isinstance(provider.source, NetworkProviderLocation):
                    raise ValueError(f"Unmanaged provider location type is not supported: {type(provider.source)}")
                return ProxyClient(httpx.AsyncClient(base_url=str(provider.source.a2a_url), timeout=None))

            provider_url = await self._deploy_manager.get_provider_url(provider_id=provider.id)
            [state] = await self._deploy_manager.state(provider_ids=[provider.id])
            should_wait = False
            match state:
                case ProviderDeploymentState.ERROR:
                    raise RuntimeError("Provider is in an error state")
                case (
                    ProviderDeploymentState.MISSING
                    | ProviderDeploymentState.RUNNING
                    | ProviderDeploymentState.STARTING
                    | ProviderDeploymentState.READY
                ):
                    async with self._uow() as uow:
                        from beeai_server.domain.repositories.env import EnvStoreEntity

                        env = await uow.env.get_all(
                            parent_entity=EnvStoreEntity.PROVIDER, parent_entity_ids=[provider.id]
                        )
                    modified = await self._deploy_manager.create_or_replace(provider=provider, env=env[provider.id])
                    should_wait = modified or state != ProviderDeploymentState.RUNNING
                case _:
                    raise ValueError(f"Unknown provider state: {state}")
            if should_wait:
                logger.info("Waiting for provider to start up...")
                await self._deploy_manager.wait_for_startup(provider_id=provider.id, timeout=self.STARTUP_TIMEOUT)
                logger.info("Provider is ready...")
            return ProxyClient(httpx.AsyncClient(base_url=str(provider_url), timeout=None))
        finally:
            unbind_contextvars("provider")
