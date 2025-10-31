# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import functools
import os
import re
import urllib.parse
from collections.abc import AsyncGenerator, Awaitable, Callable
from configparser import RawConfigParser
from contextlib import asynccontextmanager, nullcontext, suppress
from datetime import timedelta
from ssl import CERT_NONE
from typing import IO, Any, Literal

import uvicorn
import uvicorn.config as uvicorn_config
from a2a.server.agent_execution import RequestContextBuilder
from a2a.server.events import QueueManager
from a2a.server.tasks import PushNotificationConfigStore, PushNotificationSender, TaskStore
from a2a.types import AgentExtension
from fastapi import FastAPI
from fastapi.applications import AppType
from httpx import HTTPError, HTTPStatusError
from pydantic import AnyUrl
from starlette.types import Lifespan
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from agentstack_sdk.a2a.extensions import AgentDetail, AgentDetailExtensionSpec
from agentstack_sdk.a2a.extensions.services.platform import (
    _PlatformSelfRegistrationExtensionParams,
    _PlatformSelfRegistrationExtensionSpec,
)
from agentstack_sdk.platform import get_platform_client
from agentstack_sdk.platform.client import PlatformClient
from agentstack_sdk.platform.provider import Provider
from agentstack_sdk.server.agent import Agent, AgentFactory
from agentstack_sdk.server.agent import agent as agent_decorator
from agentstack_sdk.server.logging import configure_logger as configure_logger_func
from agentstack_sdk.server.logging import logger
from agentstack_sdk.server.store.context_store import ContextStore
from agentstack_sdk.server.store.memory_context_store import InMemoryContextStore
from agentstack_sdk.server.telemetry import configure_telemetry as configure_telemetry_func
from agentstack_sdk.server.utils import cancel_task


class Server:
    def __init__(self) -> None:
        self._agent_factory: AgentFactory | None = None
        self._agent: Agent | None = None
        self.server: uvicorn.Server | None = None
        self._context_store: ContextStore | None = None
        self._self_registration_client: PlatformClient | None = None
        self._self_registration_id: str | None = None
        self._provider_id: str | None = None
        self._all_configured_variables: set[str] = set()

    @functools.wraps(agent_decorator)
    def agent(*args, **kwargs) -> Callable:
        self, other_args = args[0], args[1:]  # Must hide self due to pyright issues
        if self._agent_factory:
            raise ValueError("Server can have only one agent.")

        def decorator(fn: Callable) -> Callable:
            self._agent_factory = agent_decorator(*other_args, **kwargs)(fn)  # pyright: ignore [reportArgumentType]
            return fn

        return decorator

    async def serve(
        self,
        *,
        configure_logger: bool = True,
        configure_telemetry: bool = False,
        self_registration: bool = True,
        self_registration_id: str | None = None,
        task_store: TaskStore | None = None,
        context_store: ContextStore | None = None,
        queue_manager: QueueManager | None = None,
        task_timeout: timedelta = timedelta(minutes=10),
        push_config_store: PushNotificationConfigStore | None = None,
        push_sender: PushNotificationSender | None = None,
        request_context_builder: RequestContextBuilder | None = None,
        host: str = "127.0.0.1",
        port: int = 10000,
        url: str | None = None,
        uds: str | None = None,
        fd: int | None = None,
        loop: Literal["none", "auto", "asyncio", "uvloop"] = "auto",
        http: type[asyncio.Protocol] | uvicorn_config.HTTPProtocolType = "auto",
        ws: type[asyncio.Protocol] | uvicorn_config.WSProtocolType = "auto",
        ws_max_size: int = 16 * 1024 * 1024,
        ws_max_queue: int = 32,
        ws_ping_interval: float | None = 20.0,
        ws_ping_timeout: float | None = 20.0,
        ws_per_message_deflate: bool = True,
        lifespan: uvicorn_config.LifespanType = "auto",
        lifespan_fn: Lifespan[AppType] | None = None,
        env_file: str | os.PathLike[str] | None = None,
        log_config: dict[str, Any] | str | RawConfigParser | IO[Any] | None = uvicorn_config.LOGGING_CONFIG,
        log_level: str | int | None = None,
        access_log: bool = True,
        use_colors: bool | None = None,
        interface: uvicorn_config.InterfaceType = "auto",
        reload: bool = False,
        reload_dirs: list[str] | str | None = None,
        reload_delay: float = 0.25,
        reload_includes: list[str] | str | None = None,
        reload_excludes: list[str] | str | None = None,
        workers: int | None = None,
        proxy_headers: bool = True,
        server_header: bool = True,
        date_header: bool = True,
        forwarded_allow_ips: list[str] | str | None = None,
        root_path: str = "",
        limit_concurrency: int | None = None,
        limit_max_requests: int | None = None,
        backlog: int = 2048,
        timeout_keep_alive: int = 5,
        timeout_notify: int = 30,
        timeout_graceful_shutdown: int | None = None,
        callback_notify: Callable[..., Awaitable[None]] | None = None,
        ssl_keyfile: str | os.PathLike[str] | None = None,
        ssl_certfile: str | os.PathLike[str] | None = None,
        ssl_keyfile_password: str | None = None,
        ssl_version: int = uvicorn_config.SSL_PROTOCOL_VERSION,
        ssl_cert_reqs: int = CERT_NONE,
        ssl_ca_certs: str | None = None,
        ssl_ciphers: str = "TLSv1",
        headers: list[tuple[str, str]] | None = None,
        factory: bool = False,
        h11_max_incomplete_event_size: int | None = None,
        self_registration_client_factory: Callable[[], PlatformClient] | None = None,
    ) -> None:
        if self.server:
            raise RuntimeError("The server is already running")
        if not self._agent_factory:
            raise ValueError("Agent is not registered")

        context_store = context_store or InMemoryContextStore()
        self._agent = self._agent_factory(context_store)
        self._agent.card.url = url.rstrip("/") if url else f"http://{host}:{port}"

        self._self_registration_client = (
            self_registration_client_factory() if self_registration_client_factory else None
        )
        self._self_registration_id = urllib.parse.quote(self_registration_id or self._agent.card.name)

        if headers is None:
            headers = [("server", "a2a")]
        elif not any(k.lower() == "server" for k, _ in headers):
            headers.append(("server", "a2a"))

        import uvicorn

        from agentstack_sdk.server.app import create_app

        @asynccontextmanager
        async def _lifespan_fn(app: FastAPI) -> AsyncGenerator[None, None]:
            async with self._self_registration_client or nullcontext():
                register_task = asyncio.create_task(self._register_agent()) if self_registration else None
                reload_task = asyncio.create_task(self._reload_variables_periodically()) if self_registration else None

                try:
                    async with lifespan_fn(app) if lifespan_fn else nullcontext():  # pyright: ignore [reportArgumentType]
                        yield
                finally:
                    if register_task:
                        with suppress(Exception):
                            await cancel_task(register_task)
                    if reload_task:
                        with suppress(Exception):
                            await cancel_task(reload_task)

        card_url = AnyUrl(self._agent.card.url)
        if card_url.host == "invalid":
            self._agent.card.url = f"http://{host}:{port}"

        if self_registration:
            self._agent.card.capabilities.extensions = [
                *(self._agent.card.capabilities.extensions or []),
                *_PlatformSelfRegistrationExtensionSpec(
                    _PlatformSelfRegistrationExtensionParams(self_registration_id=self._self_registration_id)
                ).to_agent_card_extensions(),
            ]

        app = create_app(
            self._agent,
            lifespan=_lifespan_fn,
            task_store=task_store,
            context_store=context_store,
            queue_manager=queue_manager,
            push_config_store=push_config_store,
            push_sender=push_sender,
            task_timeout=task_timeout,
            request_context_builder=request_context_builder,
        )

        if configure_logger:
            configure_logger_func(log_level)

        if configure_telemetry:
            configure_telemetry_func(app)

        config = uvicorn.Config(
            app,
            host,
            port,
            uds,
            fd,
            loop,
            http,
            ws,
            ws_max_size,
            ws_max_queue,
            ws_ping_interval,
            ws_ping_timeout,
            ws_per_message_deflate,
            lifespan,
            env_file,
            log_config if not configure_logger else None,
            log_level,
            access_log,
            use_colors,
            interface,
            reload,
            reload_dirs,
            reload_delay,
            reload_includes,
            reload_excludes,
            workers,
            proxy_headers,
            server_header,
            date_header,
            forwarded_allow_ips,
            root_path,
            limit_concurrency,
            limit_max_requests,
            backlog,
            timeout_keep_alive,
            timeout_notify,
            timeout_graceful_shutdown,
            callback_notify,
            ssl_keyfile,
            ssl_certfile,
            ssl_keyfile_password,
            ssl_version,
            ssl_cert_reqs,
            ssl_ca_certs,
            ssl_ciphers,
            headers,
            factory,
            h11_max_incomplete_event_size,
        )
        self.server = uvicorn.Server(config)
        await self.server.serve()

    @functools.wraps(serve)
    def run(*args, **kwargs) -> None:
        self = args[0]  # Must hide self due to pyright issues
        asyncio.run(self.serve(**kwargs))

    @property
    def should_exit(self) -> bool:
        return self.server.should_exit if self.server else False

    @should_exit.setter
    def should_exit(self, value: bool) -> None:
        if self.server:
            self.server.should_exit = value

    @property
    def _platform_url(self) -> str:
        return os.getenv("PLATFORM_URL", "http://127.0.0.1:8333")

    @property
    def _production_mode(self) -> bool:
        return os.getenv("PRODUCTION_MODE", "").lower() in ["true", "1"]

    async def _reload_variables_periodically(self):
        while True:
            await asyncio.sleep(5)
            await self._load_variables()

    async def _load_variables(self, first_run: bool = False) -> None:
        assert self.server and self._agent
        if not self._provider_id:
            return

        variables = await Provider.list_variables(self._provider_id, client=self._self_registration_client)
        old_variables = self._all_configured_variables.copy()

        for variable in list(self._all_configured_variables - variables.keys()):  # reset removed variables
            os.environ.pop(variable, None)
            self._all_configured_variables.remove(variable)

        os.environ.update(variables)
        self._all_configured_variables.update(variables.keys())

        if dirty := old_variables != self._all_configured_variables:
            logger.info(f"Environment variables reloaded dynamically: {self._all_configured_variables}")

        if first_run or dirty:
            for extension in self._agent.card.capabilities.extensions or []:
                match extension:
                    case AgentExtension(uri=AgentDetailExtensionSpec.URI, params=params):
                        variables = AgentDetail.model_validate(params).variables or []
                        if missing_keys := [env for env in variables if env.required and os.getenv(env.name) is None]:
                            logger.warning(
                                f"Missing required env variables: {missing_keys}, "
                                f"add them using `agentstack env add <agent> key=value`"
                            )

    async def _register_agent(self) -> None:
        """If not in PRODUCTION mode, register agent to the agentstack platform and provide missing env variables"""
        assert self.server and self._agent
        if self._production_mode:
            logger.debug("Agent is not automatically registered in the production mode.")
            return

        host = re.sub(r"localhost|127\.0\.0\.1", "host.docker.internal", self.server.config.host)
        provider_location = f"http://{host}:{self.server.config.port}#{self._self_registration_id}"
        logger.info("Registering agent to the agentstack platform")
        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(10),
                wait=wait_exponential(max=10),
                retry=retry_if_exception_type(HTTPError),
                reraise=True,
            ):
                with attempt:
                    try:
                        provider = await Provider.get_by_location(
                            location=provider_location, client=self._self_registration_client
                        )
                        await provider.patch(agent_card=self._agent.card, client=self._self_registration_client)
                    except HTTPStatusError as error:
                        if error.response.status_code != 404:
                            raise
                        provider = await Provider.create(
                            location=provider_location,
                            client=self._self_registration_client,
                            agent_card=self._agent.card,
                        )
                    self._provider_id = provider.id
                    logger.debug("Agent registered to the agentstack server.")
                    await self._load_variables()
                    logger.debug("Environment variables loaded dynamically.")
            logger.info("Agent registered successfully")
        except HTTPStatusError as e:
            with suppress(Exception):
                if error_message := e.response.json().get("detail"):
                    logger.info(f"Agent can not be registered to agentstack server: {error_message}")
                    return
            logger.info(f"Agent can not be registered to agentstack server: {e}")
        except HTTPError as e:
            logger.info(f"Can not reach server, check if running on {get_platform_client().base_url} : {e}")
        except Exception as e:
            logger.info(f"Agent can not be registered to agentstack server: {e}")
