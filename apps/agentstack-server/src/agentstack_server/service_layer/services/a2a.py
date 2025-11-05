# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import functools
import inspect
import logging
import uuid
from collections.abc import AsyncGenerator, AsyncIterable, AsyncIterator, Callable
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import NamedTuple, cast
from urllib.parse import urljoin, urlparse
from uuid import UUID

import httpx
from a2a.client import ClientCallContext, ClientConfig, ClientFactory
from a2a.client.base_client import BaseClient
from a2a.client.errors import A2AClientJSONRPCError
from a2a.client.transports.base import ClientTransport
from a2a.server.context import ServerCallContext
from a2a.server.events import Event
from a2a.server.request_handlers.request_handler import RequestHandler
from a2a.types import (
    AgentCard,
    DeleteTaskPushNotificationConfigParams,
    GetTaskPushNotificationConfigParams,
    InvalidRequestError,
    ListTaskPushNotificationConfigParams,
    Message,
    MessageSendParams,
    Task,
    TaskArtifactUpdateEvent,
    TaskIdParams,
    TaskNotFoundError,
    TaskPushNotificationConfig,
    TaskQueryParams,
    TaskStatusUpdateEvent,
    TransportProtocol,
)
from a2a.utils.errors import ServerError
from kink import inject
from pydantic import HttpUrl
from structlog.contextvars import bind_contextvars, unbind_contextvars

from agentstack_server.configuration import Configuration
from agentstack_server.domain.models.provider import (
    NetworkProviderLocation,
    Provider,
    ProviderDeploymentState,
)
from agentstack_server.domain.models.user import User
from agentstack_server.exceptions import EntityNotFoundError, ForbiddenUpdateError
from agentstack_server.service_layer.deployment_manager import (
    IProviderDeploymentManager,
)
from agentstack_server.service_layer.services.users import UserService
from agentstack_server.service_layer.unit_of_work import IUnitOfWorkFactory

logger = logging.getLogger(__name__)

_SUPPORTED_TRANSPORTS = {TransportProtocol.http_json, TransportProtocol.jsonrpc}


def _create_deploy_a2a_url(url: str, *, deployment_base: str) -> str:
    return urljoin(deployment_base, urlparse(url).path.lstrip("/"))


def create_deployment_agent_card(agent_card: AgentCard, *, deployment_base: str) -> AgentCard:
    proxy_interfaces = (
        [
            interface.model_copy(update={"url": _create_deploy_a2a_url(interface.url, deployment_base=deployment_base)})
            for interface in agent_card.additional_interfaces
            if interface.transport in _SUPPORTED_TRANSPORTS
        ]
        if agent_card.additional_interfaces is not None
        else None
    )
    if agent_card.preferred_transport in _SUPPORTED_TRANSPORTS:
        return agent_card.model_copy(
            update={
                "url": _create_deploy_a2a_url(agent_card.url, deployment_base=deployment_base),
                "additional_interfaces": proxy_interfaces,
            }
        )
    elif proxy_interfaces:
        interface = proxy_interfaces[0]
        return agent_card.model_copy(
            update={
                "url": interface.url,
                "preferred_transport": interface.transport,
                "additional_interfaces": proxy_interfaces,
            }
        )
    else:
        raise RuntimeError("Provider doesn't have any transport supported by the proxy.")


class A2AServerResponse(NamedTuple):
    content: bytes | None
    stream: AsyncIterable | None
    status_code: int
    headers: dict[str, str] | None
    media_type: str


def _handle_exception[T: Callable](fn: T) -> T:
    @functools.wraps(fn)
    async def _fn(*args, **kwargs):
        try:
            return await fn(*args, **kwargs)
        except EntityNotFoundError as e:
            if "task" in e.entity:
                raise ServerError(error=TaskNotFoundError()) from e
            raise
        except ForbiddenUpdateError as e:
            raise ServerError(error=InvalidRequestError(message=str(e))) from e
        except A2AClientJSONRPCError as e:
            raise ServerError(error=e.error) from e

    @functools.wraps(fn)
    async def _fn_iter(*args, **kwargs):
        try:
            async for item in fn(*args, **kwargs):
                yield item
        except A2AClientJSONRPCError as e:
            raise ServerError(error=e.error) from e

    return _fn_iter if inspect.isasyncgenfunction(fn) else _fn  # pyright: ignore [reportReturnType]


class ProxyRequestHandler(RequestHandler):
    def __init__(
        self,
        agent_card: AgentCard,
        provider_id: UUID,
        uow: IUnitOfWorkFactory,
        user: User,
    ):
        self._agent_card = agent_card
        self._provider_id = provider_id
        self._user = user
        self._uow = uow

    @asynccontextmanager
    async def _client_transport(self) -> AsyncIterator[ClientTransport]:
        async with httpx.AsyncClient(follow_redirects=True, timeout=timedelta(hours=1).total_seconds()) as httpx_client:
            client: BaseClient = cast(
                BaseClient,
                ClientFactory(config=ClientConfig(httpx_client=httpx_client)).create(card=self._agent_card),
            )
            yield client._transport

    async def _check_task(self, task_id: str):
        async with self._uow() as uow:
            await uow.a2a_requests.get_task(task_id=task_id, user_id=self._user.id)

    async def _check_and_record_request(
        self,
        task_id: str | None = None,
        context_id: str | None = None,
        allow_task_creation: bool = False,
    ):
        async with self._uow() as uow:
            # Consider: a bit paranoid check
            # if context_id:
            #     with suppress(ValueError, EntityNotFoundError):
            #         context_uuid = UUID(context_id)
            #         context = await uow.contexts.get(context_id=context_uuid)
            #         if context.created_by != self._user.id:
            #             # attempt to claim context owned by another user
            #             raise ForbiddenUpdateError(entity="a2a_request_context", id=context_id)
            await uow.a2a_requests.track_request_ids_ownership(
                user_id=self._user.id,
                provider_id=self._provider_id,
                task_id=task_id,
                context_id=context_id,
                allow_task_creation=allow_task_creation,
            )
            await uow.commit()

    def _forward_context(self, context: ServerCallContext | None = None) -> ClientCallContext:
        return ClientCallContext(state={**(context.state if context else {}), "user_id": self._user.id})

    @_handle_exception
    async def on_get_task(self, params: TaskQueryParams, context: ServerCallContext | None = None) -> Task | None:
        await self._check_task(params.id)
        async with self._client_transport() as transport:
            return await transport.get_task(params, context=self._forward_context(context))

    @_handle_exception
    async def on_cancel_task(self, params: TaskIdParams, context: ServerCallContext | None = None) -> Task | None:
        await self._check_task(params.id)
        async with self._client_transport() as transport:
            return await transport.cancel_task(params, context=self._forward_context(context))

    @_handle_exception
    async def on_message_send(
        self, params: MessageSendParams, context: ServerCallContext | None = None
    ) -> Task | Message:
        # we set task_id and context_id if not configured
        params.message.context_id = params.message.context_id or str(uuid.uuid4())
        await self._check_and_record_request(params.message.task_id, params.message.context_id)

        async with self._client_transport() as transport:
            response = await transport.send_message(params, context=self._forward_context(context))
            match response:
                case Task(id=task_id) | Message(task_id=task_id):
                    if params.message.task_id is None and task_id:
                        await self._check_and_record_request(
                            task_id, params.message.context_id, allow_task_creation=True
                        )
            return response

    @_handle_exception
    async def on_message_send_stream(
        self, params: MessageSendParams, context: ServerCallContext | None = None
    ) -> AsyncGenerator[Event]:
        # we set task_id and context_id if not configured
        params.message.context_id = params.message.context_id or str(uuid.uuid4())
        await self._check_and_record_request(params.message.task_id, params.message.context_id)
        seen_tasks = {params.message.task_id} if params.message.task_id else set()

        async with self._client_transport() as transport:
            async for event in transport.send_message_streaming(params, context=self._forward_context(context)):
                match event:
                    case (
                        TaskStatusUpdateEvent(task_id=task_id, context_id=context_id)
                        | TaskArtifactUpdateEvent(task_id=task_id, context_id=context_id)
                        | Task(id=task_id, context_id=context_id)
                        | Message(task_id=task_id, context_id=context_id)
                    ):
                        if context_id != params.message.context_id:
                            raise RuntimeError(f"Unexpected context_id returned from the agent: {context_id}")
                        if task_id and task_id not in seen_tasks:
                            await self._check_and_record_request(
                                task_id=task_id,
                                context_id=context_id,
                                allow_task_creation=True,
                            )
                            seen_tasks.add(task_id)
                yield event

    @_handle_exception
    async def on_set_task_push_notification_config(
        self,
        params: TaskPushNotificationConfig,
        context: ServerCallContext | None = None,
    ) -> TaskPushNotificationConfig:
        await self._check_task(params.task_id)
        async with self._client_transport() as transport:
            return await transport.set_task_callback(params)

    @_handle_exception
    async def on_get_task_push_notification_config(
        self,
        params: TaskIdParams | GetTaskPushNotificationConfigParams,
        context: ServerCallContext | None = None,
    ) -> TaskPushNotificationConfig:
        await self._check_task(params.id)
        async with self._client_transport() as transport:
            if isinstance(params, TaskIdParams):
                params = GetTaskPushNotificationConfigParams(id=params.id, metadata=params.metadata)
            return await transport.get_task_callback(params, context=self._forward_context(context))

    @_handle_exception
    async def on_resubscribe_to_task(
        self, params: TaskIdParams, context: ServerCallContext | None = None
    ) -> AsyncGenerator[Event]:
        await self._check_task(params.id)
        async with self._client_transport() as transport:
            async for event in transport.resubscribe(params):
                yield event

    @_handle_exception
    async def on_list_task_push_notification_config(
        self,
        params: ListTaskPushNotificationConfigParams,
        context: ServerCallContext | None = None,
    ) -> list[TaskPushNotificationConfig]:
        raise NotImplementedError("This is not supported by the client transport yet")

    @_handle_exception
    async def on_delete_task_push_notification_config(
        self,
        params: DeleteTaskPushNotificationConfigParams,
        context: ServerCallContext | None = None,
    ) -> None:
        raise NotImplementedError("This is not supported by the client transport yet")


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
        self._expire_requests_after = timedelta(days=configuration.a2a_proxy.requests_expire_after_days)

    async def get_request_handler(self, *, provider: Provider, user: User) -> RequestHandler:
        url = await self.ensure_agent(provider_id=provider.id)
        agent_card = create_deployment_agent_card(provider.agent_card, deployment_base=str(url))
        return ProxyRequestHandler(
            agent_card=agent_card,
            provider_id=provider.id,
            uow=self._uow,
            user=user,
        )

    async def expire_requests(self) -> dict[str, int]:
        async with self._uow() as uow:
            n_tasks = await uow.a2a_requests.delete_tasks(older_than=self._expire_requests_after)
            n_ctx = await uow.a2a_requests.delete_contexts(older_than=self._expire_requests_after)
            await uow.commit()
            return {"tasks": n_tasks, "contexts": n_ctx}

    async def ensure_agent(self, *, provider_id: UUID) -> HttpUrl:
        try:
            bind_contextvars(provider=provider_id)

            async with self._uow() as uow:
                provider = await uow.providers.get(provider_id=provider_id)
                await uow.providers.update_last_accessed(provider_id=provider_id)
                await uow.commit()

            if not provider.managed:
                assert isinstance(provider.source, NetworkProviderLocation)
                return provider.source.a2a_url

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
                        from agentstack_server.domain.repositories.env import (
                            EnvStoreEntity,
                        )

                        env = await uow.env.get_all(
                            parent_entity=EnvStoreEntity.PROVIDER,
                            parent_entity_ids=[provider.id],
                        )
                    modified = await self._deploy_manager.create_or_replace(provider=provider, env=env[provider.id])
                    should_wait = modified or state != ProviderDeploymentState.RUNNING
                case _:
                    raise ValueError(f"Unknown provider state: {state}")
            if should_wait:
                logger.info("Waiting for provider to start up...")
                await self._deploy_manager.wait_for_startup(provider_id=provider.id, timeout=self.STARTUP_TIMEOUT)
                logger.info("Provider is ready...")
            return provider_url
        finally:
            unbind_contextvars("provider")
