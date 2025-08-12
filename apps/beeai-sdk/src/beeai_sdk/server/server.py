# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import functools
import os
import re
from collections.abc import AsyncGenerator, Awaitable, Callable
from configparser import RawConfigParser
from contextlib import asynccontextmanager, nullcontext, suppress
from ssl import CERT_NONE
from typing import IO, Any
from urllib.parse import urljoin

import httpx
import uvicorn
import uvicorn.config as uvicorn_config
from a2a.server.agent_execution import RequestContextBuilder
from a2a.server.events import QueueManager
from a2a.server.tasks import PushNotificationConfigStore, PushNotificationSender, TaskStore
from a2a.types import AgentExtension
from fastapi import FastAPI
from fastapi.applications import AppType
from httpx import AsyncClient, HTTPError, HTTPStatusError
from sse_starlette.sse import AppStatus
from starlette.types import Lifespan
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from beeai_sdk.server.agent import Agent
from beeai_sdk.server.agent import agent as agent_decorator
from beeai_sdk.server.logging import configure_logger as configure_logger_func
from beeai_sdk.server.logging import logger
from beeai_sdk.server.telemetry import configure_telemetry as configure_telemetry_func
from beeai_sdk.server.utils import cancel_task


class Server:
    def __init__(self) -> None:
        self._agent: Agent | None = None
        self.server: uvicorn.Server | None = None
        self._self_registration_client: httpx.AsyncClient | None = None

    @functools.wraps(agent_decorator)
    def agent(*args, **kwargs) -> Callable:
        self, other_args = args[0], args[1:]  # Must hide self due to pyright issues
        if self._agent:
            raise ValueError("Server can have only one agent.")

        def decorator(fn: Callable) -> Callable:
            self._agent = agent_decorator(*other_args, **kwargs)(fn)  # pyright: ignore [reportArgumentType]
            return fn

        return decorator

    async def serve(
        self,
        *,
        configure_logger: bool = True,
        configure_telemetry: bool = False,
        self_registration: bool = True,
        task_store: TaskStore | None = None,
        queue_manager: QueueManager | None = None,
        push_config_store: PushNotificationConfigStore | None = None,
        push_sender: PushNotificationSender | None = None,
        request_context_builder: RequestContextBuilder | None = None,
        host: str = "127.0.0.1",
        port: int = 10000,
        uds: str | None = None,
        fd: int | None = None,
        loop: uvicorn_config.LoopSetupType = "auto",
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
        self_registration_client: httpx.AsyncClient | None = None,
    ) -> None:
        if self.server:
            raise RuntimeError("The server is already running")
        if not self._agent:
            raise ValueError("Agent is not registered")

        self._self_registration_client = self_registration_client

        # This is a global loop-bound event that would break the application
        # if it's run a second time in a different loop
        # https://github.com/sysid/sse-starlette/issues/140
        AppStatus.should_exit_event = None

        if headers is None:
            headers = [("server", "a2a")]
        elif not any(k.lower() == "server" for k, _ in headers):
            headers.append(("server", "a2a"))

        import uvicorn

        from beeai_sdk.server.app import create_app

        @asynccontextmanager
        async def _lifespan_fn(app: FastAPI) -> AsyncGenerator[None, None]:
            register_task = asyncio.create_task(self._register_agent()) if self_registration else None
            try:
                async with lifespan_fn(app) if lifespan_fn else nullcontext():  # pyright: ignore [reportArgumentType]
                    yield
            finally:
                if register_task:
                    await cancel_task(register_task)

        self._agent.card.url = f"http://{host}:{port}"

        app = create_app(
            self._agent,
            lifespan=_lifespan_fn,
            task_store=task_store,
            queue_manager=queue_manager,
            push_config_store=push_config_store,
            push_sender=push_sender,
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

    async def _register_agent(self) -> None:
        """If not in PRODUCTION mode, register agent to the beeai platform and provide missing env variables"""
        assert self.server and self._agent
        if os.getenv("PRODUCTION_MODE", "").lower() in ["true", "1"]:
            logger.debug("Agent is not automatically registered in the production mode.")
            return

        url = os.getenv("PLATFORM_URL", "http://127.0.0.1:8333")
        host = re.sub(r"localhost|127\.0\.0\.1", "host.docker.internal", self.server.config.host)
        request_data = {"location": f"http://{host}:{self.server.config.port}"}
        logger.info("Registering agent to the beeai platform")
        try:
            envs = {}
            async with self._self_registration_client or AsyncClient() as client:
                async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(10),
                    wait=wait_exponential(max=10),
                    retry=retry_if_exception_type(HTTPError),
                    reraise=True,
                ):
                    base_url = "" if str(client.base_url) else urljoin(url, "/api/v1/")
                    with attempt:
                        resp = await client.get(urljoin(base_url, "providers"))
                        resp.raise_for_status()

                        resp = await client.post(
                            urljoin(base_url, "providers"), json=request_data, params={"auto_remove": True}
                        )
                        resp.raise_for_status()

                        logger.debug("Agent registered to the beeai server.")

                        env_resp = await client.get(urljoin(base_url, "variables"))
                        envs_request = env_resp.raise_for_status().json()

                        envs = envs_request.get("env")
                        os.environ["LLM_MODEL"] = "dummy"
                        os.environ["LLM_API_KEY"] = "dummy"
                        os.environ["LLM_API_BASE"] = f"{url.rstrip('/')}/api/v1/llm"

                for extension in self._agent.card.capabilities.extensions or []:
                    # TODO - env extension?
                    match extension:
                        case AgentExtension(
                            uri="https://a2a-extensions.beeai.dev/variables",
                            params=params,
                            required=required,
                        ):
                            # register all available envs
                            missing_keyes = []
                            for env in (params or {}).get("env", {}):
                                # Those envs are set to use LLM gateway from platform server
                                if env["name"] in {"LLM_MODEL", "LLM_API_KEY", "LLM_API_BASE"}:
                                    continue
                                server_env = envs.get(env.get("name"))
                                if server_env:
                                    logger.debug(f"Env variable {env['name']} = '{server_env}' added dynamically")
                                    os.environ[env["name"]] = server_env
                                elif env.get("required"):
                                    missing_keyes.append(env)
                            if len(missing_keyes) and required:
                                logger.debug(f"Can not run agent, missing required env variables: {missing_keyes}")
                                raise Exception("Missing env variables")
            logger.info("Agent registered successfully")
        except HTTPStatusError as e:
            with suppress(Exception):
                if error_message := e.response.json().get("detail"):
                    logger.info(f"Agent can not be registered to beeai server: {error_message}")
                    return
            logger.info(f"Agent can not be registered to beeai server: {e}")
        except HTTPError as e:
            logger.info(f"Can not reach server, check if running on {url} : {e}")
        except Exception as e:
            logger.info(f"Agent can not be registered to beeai server: {e}")
