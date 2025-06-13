# Copyright 2025 © BeeAI a Series of LF Projects, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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


class AcpProxyClient(NamedTuple):
    client: httpx.AsyncClient
    provider: Provider
    agent: Agent
    user: User
    run_id: UUID | None = None


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
    async def get_proxy_client(self, *, agent_name: str, run_id: None = None, user: User) -> httpx.AsyncClient: ...
    @overload
    async def get_proxy_client(self, *, agent_name: None = None, run_id: UUID, user: User) -> httpx.AsyncClient: ...
    async def get_proxy_client(self, *, agent_name: str = None, run_id: None = None, user: User) -> AcpProxyClient:
        try:
            if not (bool(agent_name) ^ bool(run_id)):
                raise ValueError("Exactly one of agent_name or run_id must be provided")
            async with self._uow() as uow:
                if agent_name:
                    agent = await uow.agents.get_agent_by_name(name=agent_name)
                else:
                    agent = await uow.agents.find_by_acp_run_id(run_id=run_id, user_id=user.id)
                provider = await uow.providers.get(provider_id=agent.provider_id)
            bind_contextvars(provider=provider.id)

            if not provider.managed:
                client = httpx.AsyncClient(base_url=str(provider.source.root), timeout=None)
                return AcpProxyClient(client=client, provider=provider, agent=agent, run_id=run_id, user=user)

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
                    should_wait = await self._deploy_manager.create_or_replace(provider=provider, env=env)
                case _:
                    raise ValueError(f"Unknown provider state: {state}")
            if should_wait:
                logger.info("Waiting for provider to start up...")
                await self._deploy_manager.wait_for_startup(provider_id=provider.id, timeout=self.STARTUP_TIMEOUT)
                logger.info("Provider is ready...")
            client = httpx.AsyncClient(base_url=str(provider_url), timeout=None)
            return AcpProxyClient(client=client, provider=provider, agent=agent, run_id=run_id, user=user)
        except EntityNotFoundError as ex:
            if ex.entity in {"agent", "agent_run"}:
                raise ACPError(
                    error=Error(code=ErrorCode.NOT_FOUND, message=f"{ex.entity} '{ex.id}' not found")
                ) from ex
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
        client: AcpProxyClient,
        method: str,
        url: str,
        payload: BaseModel | None = None,
    ):
        exit_stack = AsyncExitStack()
        json = payload and self._replace_template_content_url(payload, client.provider).model_dump(mode="json")
        client, agent, user, run_id = client.client, client.agent, client.user, client.run_id
        try:
            client = await exit_stack.enter_async_context(client)
            request = AgentRunRequest(acp_run_id=run_id, agent_id=agent.id, created_by=user.id)

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
            if is_stream and run_id is None and "Run-ID" in resp.headers:
                async with self._uow() as uow:
                    request.acp_run_id = UUID(resp.headers["Run-ID"])
                    await uow.agents.update_request(request=request)
                    await uow.commit()
            else:
                request.acp_run_id = resp.headers.get("Run-ID", run_id)

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
