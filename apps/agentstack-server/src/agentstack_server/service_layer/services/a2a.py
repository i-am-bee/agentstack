# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import functools
import inspect
import logging
import uuid
from collections.abc import AsyncGenerator, AsyncIterable, AsyncIterator, Awaitable, Callable, Coroutine, Iterator
from contextlib import asynccontextmanager, contextmanager
from datetime import timedelta
from typing import Any, NamedTuple, cast, overload, override
from urllib.parse import urljoin, urlparse
from uuid import UUID

import httpx
from a2a.client import ClientCallContext, ClientConfig, ClientFactory
from a2a.client.base_client import BaseClient
from a2a.client.transports.base import ClientTransport
from a2a.server.context import ServerCallContext
from a2a.server.events import Event
from a2a.server.request_handlers.request_handler import RequestHandler
from a2a.types import (
    AgentCard,
    AgentInterface,
    CancelTaskRequest,
    CreateTaskPushNotificationConfigRequest,
    DeleteTaskPushNotificationConfigRequest,
    GetTaskPushNotificationConfigRequest,
    GetTaskRequest,
    InternalError,
    InvalidRequestError,
    ListTaskPushNotificationConfigsRequest,
    ListTaskPushNotificationConfigsResponse,
    ListTasksRequest,
    ListTasksResponse,
    Message,
    SendMessageRequest,
    StreamResponse,
    SubscribeToTaskRequest,
    Task,
    TaskNotFoundError,
    TaskPushNotificationConfig,
)
from a2a.utils.errors import A2AError
from google.protobuf.json_format import ParseDict
from kink import inject
from opentelemetry import trace
from pydantic import HttpUrl
from starlette.datastructures import URL
from structlog.contextvars import bind_contextvars, unbind_contextvars

from agentstack_server.api.auth.auth import exchange_internal_jwt
from agentstack_server.api.auth.utils import create_resource_uri
from agentstack_server.configuration import Configuration
from agentstack_server.domain.models.provider import (
    NetworkProviderLocation,
    Provider,
    ProviderDeploymentState,
    UnmanagedState,
)
from agentstack_server.domain.models.user import User
from agentstack_server.exceptions import EntityNotFoundError, ForbiddenUpdateError, InvalidProviderCallError
from agentstack_server.service_layer.deployment_manager import (
    IProviderDeploymentManager,
)
from agentstack_server.service_layer.services.users import UserService
from agentstack_server.service_layer.unit_of_work import IUnitOfWorkFactory
from agentstack_server.telemetry import INSTRUMENTATION_NAME

logger = logging.getLogger(__name__)

_SUPPORTED_TRANSPORTS = {"HTTP+JSON", "JSONRPC"}


def _create_deploy_a2a_url(url: str, *, deployment_base: str) -> str:
    return urljoin(deployment_base, urlparse(url).path.lstrip("/"))


def create_deployment_agent_card(agent_card: dict[str, Any], *, deployment_base: str) -> AgentCard:
    card_copy = AgentCard()
    ParseDict(agent_card, card_copy, ignore_unknown_fields=True)

    new_interfaces = []
    for interface in card_copy.supported_interfaces:
        if interface.protocol_binding in _SUPPORTED_TRANSPORTS:
            new_interface = AgentInterface()
            new_interface.CopyFrom(interface)
            new_interface.url = _create_deploy_a2a_url(interface.url, deployment_base=deployment_base)
            new_interfaces.append(new_interface)

    if not new_interfaces:
        raise RuntimeError("Provider doesn't have any transport supported by the proxy.")

    del card_copy.supported_interfaces[:]
    card_copy.supported_interfaces.extend(new_interfaces)

    return card_copy


class A2AServerResponse(NamedTuple):
    content: bytes | None
    stream: AsyncIterable | None
    status_code: int
    headers: dict[str, str] | None
    media_type: str


@overload
def _handle_exception[**P, T](fn: Callable[P, AsyncGenerator[T]]) -> Callable[P, AsyncGenerator[T]]: ...


@overload
def _handle_exception[**P, T](fn: Callable[P, Coroutine[Any, Any, T]]) -> Callable[P, Coroutine[Any, Any, T]]: ...


def _handle_exception[**P, T](
    fn: Callable[P, AsyncGenerator[T]] | Callable[P, Coroutine[Any, Any, T]],
) -> Callable[P, AsyncGenerator[T]] | Callable[P, Coroutine[Any, Any, T]]:
    @contextmanager
    def _handle_exception_impl() -> Iterator[None]:
        try:
            yield
        except EntityNotFoundError as e:
            if "task" in e.entity:
                raise TaskNotFoundError() from e
            raise
        except ForbiddenUpdateError as e:
            raise InvalidRequestError(message=str(e)) from e
        except A2AError:
            raise
        except InvalidProviderCallError as e:
            raise InvalidRequestError(message=f"Invalid request to agent: {e!r}") from e
        except Exception as e:
            raise InternalError(message=f"Internal error: {e!r}") from e

    if inspect.isasyncgenfunction(fn):

        @functools.wraps(cast(Callable[P, AsyncGenerator[T]], fn))
        async def _fn_iter(*args: P.args, **kwargs: P.kwargs) -> AsyncGenerator[T]:
            with _handle_exception_impl():
                async for item in fn(*args, **kwargs):  # type: ignore[misc]
                    yield item

        return _fn_iter
    else:

        @functools.wraps(cast(Callable[P, Awaitable[T]], fn))
        async def _fn(*args: P.args, **kwargs: P.kwargs) -> T:
            with _handle_exception_impl():
                return await fn(*args, **kwargs)  # type: ignore[return-value]

        return _fn


class ProxyRequestHandler(RequestHandler):
    def __init__(
        self,
        *,
        provider_id: UUID,
        uow: IUnitOfWorkFactory,
        user: User,
        # Calling the factory have side-effects, such as rotating the agent
        agent_card_factory: Callable[[], Awaitable[AgentCard]] | None = None,
        agent_card: AgentCard | None = None,
        configuration: Configuration,
    ):
        if agent_card_factory is None and agent_card is None:
            raise ValueError("One of agent_card_factory or agent_card must be provided")
        self._configuration = configuration
        self._agent_card_factory = agent_card_factory
        self._agent_card = agent_card
        self._provider_id = provider_id
        self._user = user
        self._uow = uow

    @asynccontextmanager
    async def _client_transport(self, context: ServerCallContext | None = None) -> AsyncIterator[ClientTransport]:
        from fastapi.security.utils import get_authorization_scheme_param

        if self._agent_card is None:
            assert self._agent_card_factory is not None
            self._agent_card = await self._agent_card_factory()

        headers: dict[str, str] = {} if not context else context.state.get("headers", {})
        headers.pop("host", None)
        headers.pop("content-length", None)
        if auth_header := headers.get("authorization"):
            _scheme, header_token = get_authorization_scheme_param(auth_header)
            try:
                audience = create_resource_uri(URL(self._agent_card.supported_interfaces[0].url))
                token, _ = exchange_internal_jwt(header_token, self._configuration, audience=[audience])
                headers["authorization"] = f"Bearer {token}"
            except Exception:
                headers.pop("authorization", None)  # forward header only if it's a valid context token

        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=timedelta(hours=1).total_seconds(),
            headers=headers,
        ) as httpx_client:
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
        trace_id: str | None = None,
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
                trace_id=trace_id,
                allow_task_creation=allow_task_creation,
            )
            await uow.commit()

    def _forward_context(self, context: ServerCallContext | None = None) -> ClientCallContext:
        return ClientCallContext(state={**(context.state if context else {}), "user_id": self._user.id})

    def _response_to_event(self, response: StreamResponse) -> tuple[str, str, Event]:
        if response.HasField("status_update"):
            task_id = response.status_update.task_id
            context_id = response.status_update.context_id
            result_event = response.status_update
        elif response.HasField("artifact_update"):
            task_id = response.artifact_update.task_id
            context_id = response.artifact_update.context_id
            result_event = response.artifact_update
        elif response.HasField("task"):
            task_id = response.task.id
            context_id = response.task.context_id
            result_event = response.task
        elif response.HasField("message"):
            task_id = response.message.task_id
            context_id = response.message.context_id
            result_event = response.message
        else:
            raise ValueError("Unknown event type")
        return task_id, context_id, result_event

    @_handle_exception
    @override
    async def on_get_task(self, params: GetTaskRequest, context: ServerCallContext | None = None) -> Task | None:
        await self._check_task(params.id)
        async with self._client_transport(context) as transport:
            return await transport.get_task(params, context=self._forward_context(context))

    @_handle_exception
    @override
    async def on_cancel_task(self, params: CancelTaskRequest, context: ServerCallContext | None = None) -> Task | None:
        await self._check_task(params.id)
        async with self._client_transport(context) as transport:
            return await transport.cancel_task(params, context=self._forward_context(context))

    @_handle_exception
    @override
    async def on_message_send(
        self, params: SendMessageRequest, context: ServerCallContext | None = None
    ) -> Task | Message:
        # we set task_id and context_id if not configured
        with trace.get_tracer(INSTRUMENTATION_NAME).start_as_current_span("on_message_send") as span:
            trace_id = hex(span.get_span_context().trace_id)[2:]
            params.message.context_id = params.message.context_id or str(uuid.uuid4())
            await self._check_and_record_request(params.message.task_id, params.message.context_id, trace_id=trace_id)

            async with self._client_transport(context) as transport:
                response = await transport.send_message(params, context=self._forward_context(context))
                if task_id := response.task.id or response.message.task_id:
                    await self._check_and_record_request(
                        task_id, params.message.context_id, allow_task_creation=True, trace_id=trace_id
                    )
                if response.HasField("task"):
                    return response.task
                return response.message

    @_handle_exception
    @override
    async def on_message_send_stream(
        self, params: SendMessageRequest, context: ServerCallContext | None = None
    ) -> AsyncGenerator[Event]:
        with trace.get_tracer(INSTRUMENTATION_NAME).start_as_current_span("on_message_send_stream") as span:
            # we set task_id and context_id if not configured
            trace_id = hex(span.get_span_context().trace_id)[2:]
            params.message.context_id = params.message.context_id or str(uuid.uuid4())
            await self._check_and_record_request(params.message.task_id, params.message.context_id, trace_id=trace_id)

            seen_tasks = {params.message.task_id} if params.message.task_id else set()

            async with self._client_transport(context) as transport:
                async for event in transport.send_message_streaming(params, context=self._forward_context(context)):
                    task_id, context_id, result_event = self._response_to_event(event)
                    if context_id != params.message.context_id:
                        raise RuntimeError(f"Unexpected context_id returned from the agent: {context_id}")
                    if task_id and task_id not in seen_tasks:
                        await self._check_and_record_request(
                            task_id=task_id,
                            trace_id=trace_id,
                            context_id=context_id,
                            allow_task_creation=True,
                        )
                        seen_tasks.add(task_id)
                    yield result_event

    @_handle_exception
    @override
    async def on_create_task_push_notification_config(
        self,
        params: CreateTaskPushNotificationConfigRequest,
        context: ServerCallContext | None = None,
    ) -> TaskPushNotificationConfig:
        await self._check_task(params.task_id)
        async with self._client_transport(context) as transport:
            return await transport.create_task_push_notification_config(params, context=self._forward_context(context))

    @_handle_exception
    @override
    async def on_get_task_push_notification_config(
        self,
        params: GetTaskPushNotificationConfigRequest,
        context: ServerCallContext | None = None,
    ) -> TaskPushNotificationConfig:
        await self._check_task(params.task_id)
        async with self._client_transport(context) as transport:
            return await transport.get_task_push_notification_config(params, context=self._forward_context(context))

    @_handle_exception
    @override
    async def on_subscribe_to_task(
        self,
        params: SubscribeToTaskRequest,
        context: ServerCallContext | None = None,
    ) -> AsyncGenerator[Event]:
        await self._check_task(params.id)
        async with self._client_transport(context) as transport:
            async for event in transport.subscribe(params):
                _, _, result_event = self._response_to_event(event)
                yield result_event

    @_handle_exception
    @override
    async def on_list_task_push_notification_configs(
        self,
        params: ListTaskPushNotificationConfigsRequest,
        context: ServerCallContext | None = None,
    ) -> ListTaskPushNotificationConfigsResponse:
        raise NotImplementedError("This is not supported by the client transport yet")

    @_handle_exception
    async def on_delete_task_push_notification_config(
        self,
        params: DeleteTaskPushNotificationConfigRequest,
        context: ServerCallContext | None = None,
    ) -> None:
        raise NotImplementedError("This is not supported by the client transport yet")
        # await self._check_task(params.task_id)
        # async with self._client_transport(context) as transport:
        #     await transport.delete_task_push_notification_config(params)

    @_handle_exception
    @override
    async def on_list_tasks(
        self,
        params: ListTasksRequest,
        context: ServerCallContext | None = None,
    ) -> ListTasksResponse:
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
        async def agent_card_factory() -> AgentCard:
            # Delay ensure_agent to the handler so that errors are wrapped properly
            url = await self.ensure_agent(provider_id=provider.id)
            return create_deployment_agent_card(provider.agent_card, deployment_base=str(url))

        return ProxyRequestHandler(
            agent_card_factory=agent_card_factory,
            provider_id=provider.id,
            uow=self._uow,
            user=user,
            configuration=self._config,
        )

    async def expire_requests(self) -> dict[str, int]:
        if self._expire_requests_after <= timedelta(days=0):
            return {"tasks": 0, "contexts": 0}
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
                if provider.unmanaged_state is UnmanagedState.OFFLINE:
                    raise InvalidProviderCallError(
                        f"Cannot send message to provider {provider_id}: provider is offline"
                    )

                assert isinstance(provider.source, NetworkProviderLocation)
                return provider.source.a2a_url

            provider_url = await self._deploy_manager.get_provider_url(provider_id=provider.id)
            [state] = await self._deploy_manager.state(provider_ids=[provider.id])
            should_wait = False
            match state:
                case ProviderDeploymentState.ERROR:
                    raise InvalidProviderCallError(
                        f"Cannot send message to provider {provider_id}: provider is in an error state"
                    )
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
