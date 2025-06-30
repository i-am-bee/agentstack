# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from contextlib import AsyncExitStack
from datetime import timedelta
from typing import overload, NamedTuple, AsyncIterable
from uuid import UUID

import httpx
from acp_sdk import ACPError, Error, ErrorCode, RunCreateRequest, RunResumeRequest
from kink import inject
from pydantic import BaseModel, AnyUrl
from structlog.contextvars import bind_contextvars, unbind_contextvars

from beeai_server.configuration import Configuration
from beeai_server.domain.models.user import User
from beeai_server.service_layer.deployment_manager import IProviderDeploymentManager
from beeai_server.domain.models.agent import AgentRunRequest, Agent
from beeai_server.domain.models.provider import ProviderDeploymentState, Provider
from beeai_server.exceptions import EntityNotFoundError
from beeai_server.service_layer.services.users import UserService
from beeai_server.service_layer.unit_of_work import IUnitOfWorkFactory

logger = logging.getLogger(__name__)


class AcpServerResponse(NamedTuple):
    content: bytes | None
    stream: AsyncIterable | None
    status_code: int
    headers: dict[str, str] | None
    media_type: str


class ProxyRequestContext(NamedTuple):
    client: httpx.AsyncClient
    provider: Provider
    agent: Agent
    user: User
    run_id: UUID | None = None
    session_id: UUID | None = None


@inject
class AcpProxyService:
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

    @overload
    async def get_proxy_context(
        self, *, agent_name: None = None, run_id: None = None, session_id: UUID, user: User
    ) -> httpx.AsyncClient: ...
    @overload
    async def get_proxy_context(
        self, *, agent_name: str, run_id: None = None, session_id: None = None, user: User
    ) -> httpx.AsyncClient: ...
    @overload
    async def get_proxy_context(
        self, *, agent_name: None = None, run_id: UUID, session_id: None = None, user: User
    ) -> httpx.AsyncClient: ...
    async def get_proxy_context(
        self, *, agent_name: str | None = None, run_id: UUID | None = None, session_id: UUID | None = None, user: User
    ) -> ProxyRequestContext:
        try:
            if bool(agent_name) + bool(run_id) + bool(session_id) > 1:
                raise ValueError("Exactly one of agent_name, run_id or session_id must be provided")
            async with self._uow() as uow:
                if agent_name:
                    agent = await uow.agents.get_agent_by_name(name=agent_name)
                elif run_id:
                    agent = await uow.agents.find_by_acp_run_id(run_id=run_id, user_id=user.id)
                else:
                    agent = await uow.agents.find_by_acp_session_id(session_id=session_id, user_id=user.id)

                provider = await uow.providers.get(provider_id=agent.provider_id)
            bind_contextvars(provider=provider.id)

            if not provider.managed:
                client = httpx.AsyncClient(base_url=str(provider.source.root), timeout=None)
                return ProxyRequestContext(
                    client=client, provider=provider, agent=agent, run_id=run_id, session_id=session_id, user=user
                )

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
            client = httpx.AsyncClient(base_url=str(provider_url), timeout=None)
            return ProxyRequestContext(client=client, provider=provider, agent=agent, run_id=run_id, user=user)
        except EntityNotFoundError as ex:
            if ex.entity in {"agent", "agent_run"}:
                raise ACPError(error=Error(code=ErrorCode.NOT_FOUND, message=str(ex))) from ex
            raise
        finally:
            unbind_contextvars("provider")

    def _replace_template_content_url(self, request: BaseModel, provider: Provider) -> BaseModel:
        """
        Replace all {platform_url} template strings with the actual platform url based on the provider source
        (in cluster or self-registered)

        TODO: temporary until a proper implementation in beeai-sdk
        """
        request = request.model_copy(deep=True)
        platform_url = (
            "localhost:8333"  # this is the port-forwarded port to beeai-platform, can be different from config.port
            if provider.source.is_on_host
            else self._config.platform_service_url
        )
        match request:
            case RunCreateRequest():
                for part in (part for message in request.input for part in message.parts if part.content_url):
                    part.content_url = AnyUrl(str(part.content_url).replace("{platform_url}", platform_url))
            case RunResumeRequest():
                for part in (p for p in request.await_resume.message.parts if p.content_url):
                    part.content_url = AnyUrl(str(part.content_url).replace("{platform_url}", platform_url))
        return request

    async def send_request(
        self,
        context: ProxyRequestContext,
        method: str,
        url: str,
        payload: BaseModel | None = None,
    ):
        exit_stack = AsyncExitStack()
        json = payload and self._replace_template_content_url(payload, context.provider).model_dump(mode="json")
        try:
            client = await exit_stack.enter_async_context(context.client)
            request = AgentRunRequest(
                acp_run_id=context.run_id,
                agent_id=context.agent.id,
                created_by=context.user.id,
                acp_session_id=context.session_id,
            )

            # Create a new run request
            async with self._uow() as uow:
                await uow.agents.create_request(request=request)
                await uow.commit()

            async def finalize_request():
                async with self._uow() as uow:
                    request.set_finished()
                    await uow.agents.update_request(request=request)
                    await uow.commit()

            exit_stack.push_async_callback(finalize_request)

            resp: httpx.Response = await exit_stack.enter_async_context(client.stream(method, url, json=json))
            is_stream = resp.headers["content-type"].startswith("text/event-stream")

            # For stream, save a new run ID to a database immediately
            if is_stream and context.run_id is None and "Run-ID" in resp.headers:
                async with self._uow() as uow:
                    request.acp_run_id = resp.headers["Run-ID"]
                    request.acp_session_id = resp.headers.get("Session-ID", None)
                    await uow.agents.update_request(request=request)
                    await uow.commit()
            else:
                request.acp_run_id = resp.headers.get("Run-ID", context.run_id)
                request.acp_session_id = resp.headers.get("Session-ID", context.session_id)

            async def stream_fn():
                try:
                    async for event in resp.stream:
                        yield event
                finally:
                    await exit_stack.pop_all().aclose()

            common = dict(status_code=resp.status_code, headers=resp.headers, media_type=resp.headers["content-type"])
            if is_stream:
                return AcpServerResponse(content=None, stream=stream_fn(), **common)
            else:
                try:
                    await resp.aread()
                    return AcpServerResponse(stream=None, content=resp.content, **common)
                finally:
                    await exit_stack.pop_all().aclose()
        except BaseException:
            await exit_stack.pop_all().aclose()
            raise

    async def list_agents(self) -> list[Agent]:
        async with self._uow() as uow:
            return [agent async for agent in uow.agents.list()]

    async def get_agent_by_name(self, name: str) -> Agent:
        async with self._uow() as uow:
            return await uow.agents.get_agent_by_name(name=name)
