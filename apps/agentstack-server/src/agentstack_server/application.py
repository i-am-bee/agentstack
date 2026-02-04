# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
import time
from collections.abc import Iterable
from contextlib import asynccontextmanager, nullcontext, suppress
from importlib.metadata import PackageNotFoundError, version

import procrastinate
from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, ORJSONResponse
from kink import Container, di, inject
from limits.aio.storage import Storage
from opentelemetry.metrics import CallbackOptions, Observation, get_meter
from procrastinate.exceptions import AlreadyEnqueued
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_500_INTERNAL_SERVER_ERROR

from agentstack_server.api.middleware.proxy_headers import ProxyHeadersMiddleware
from agentstack_server.api.middleware.rate_limit import RateLimitMiddleware
from agentstack_server.api.routes.a2a import router as a2a_router
from agentstack_server.api.routes.auth import well_known_router as auth_well_known_router
from agentstack_server.api.routes.configurations import router as configuration_router
from agentstack_server.api.routes.connectors import router as connectors_router
from agentstack_server.api.routes.contexts import router as contexts_router
from agentstack_server.api.routes.files import router as files_router
from agentstack_server.api.routes.model_providers import router as model_providers_router
from agentstack_server.api.routes.openai import router as openai_router
from agentstack_server.api.routes.provider_builds import router as provider_builds_router
from agentstack_server.api.routes.provider_discovery import router as provider_discovery_router
from agentstack_server.api.routes.providers import router as provider_router
from agentstack_server.api.routes.user import router as user_router
from agentstack_server.api.routes.user_feedback import router as user_feedback_router
from agentstack_server.api.routes.users import router as users_router
from agentstack_server.api.routes.variables import router as variables_router
from agentstack_server.api.routes.vector_stores import router as vector_stores_router
from agentstack_server.api.utils import format_openai_error
from agentstack_server.bootstrap import bootstrap_dependencies_sync
from agentstack_server.configuration import Configuration
from agentstack_server.exceptions import (
    PlatformError,
    RateLimitExceededError,
)
from agentstack_server.jobs.crons.model_provider import check_model_provider_registry, update_model_state_and_cache
from agentstack_server.jobs.crons.provider import check_registry
from agentstack_server.run_workers import run_workers
from agentstack_server.service_layer.services.user_feedback import UserFeedbackService
from agentstack_server.telemetry import INSTRUMENTATION_NAME, shutdown_telemetry

logger = logging.getLogger(__name__)


def get_version():
    try:
        __version__ = version("agentstack-server")
    except PackageNotFoundError:
        __version__ = "0.1.0"

    return __version__


def extract_messages(exc):
    if isinstance(exc, BaseExceptionGroup):
        return [(exc_type, msg) for e in exc.exceptions for exc_type, msg in extract_messages(e)]
    else:
        return [(type(exc).__name__, str(exc))]


def register_global_exception_handlers(app: FastAPI):
    @app.exception_handler(PlatformError)
    @app.exception_handler(Exception)
    @app.exception_handler(HTTPException)
    async def custom_http_exception_handler(request: Request, exc: Exception):
        """Include detail in all unhandled exceptions.

        This is not the beset security practice as it can reveal details about the internal workings of this service,
        but this is an open-source service anyway, so the risk is acceptable
        """

        logger.error("Error during HTTP request: %s", repr(extract_messages(exc)))

        match exc:
            case RateLimitExceededError():
                exception = HTTPException(
                    status_code=exc.status_code,
                    detail=str(exc),
                    headers={
                        "X-RateLimit-Limit": str(exc.amount),
                        "X-RateLimit-Remaining": str(exc.remaining),
                        "X-RateLimit-Reset": str(exc.reset_time),
                        "Retry-After": str(int(exc.reset_time - time.time())),
                    },
                )
            case PlatformError():
                exception = HTTPException(status_code=exc.status_code, detail=str(exc))
            case HTTPException():
                exception = exc
            case _:
                exception = HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, detail=repr(extract_messages(exc)))

        if exception.status_code == HTTP_401_UNAUTHORIZED:
            exception.headers = {
                **(exception.headers or {}),
                "WWW-Authenticate": f'Bearer resource_metadata="{request.url.replace(path="/.well-known/oauth-protected-resource")}"',  # We don't define multiple resource domains at the moment
            }

        if request.url.path.startswith("/api/v1/openai"):
            return JSONResponse(
                status_code=exception.status_code,
                headers=exception.headers,
                content=format_openai_error(exc),
            )

        return await http_exception_handler(request, exception)


def mount_routes(app: FastAPI):
    server_router = APIRouter()
    server_router.include_router(user_router, prefix="/user")
    server_router.include_router(users_router, prefix="/users")
    server_router.include_router(a2a_router, prefix="/a2a")
    server_router.include_router(provider_router, prefix="/providers", tags=["providers"])
    server_router.include_router(provider_discovery_router, prefix="/providers/discovery", tags=["provider_discovery"])
    server_router.include_router(provider_builds_router, prefix="/provider_builds", tags=["provider_builds"])
    server_router.include_router(model_providers_router, prefix="/model_providers", tags=["model_providers"])
    server_router.include_router(configuration_router, prefix="/configurations", tags=["configurations"])
    server_router.include_router(files_router, prefix="/files", tags=["files"])
    server_router.include_router(variables_router, prefix="/variables", tags=["variables"])
    server_router.include_router(contexts_router, prefix="/contexts", tags=["contexts"])
    server_router.include_router(openai_router, prefix="/openai", tags=["openai"])
    server_router.include_router(vector_stores_router, prefix="/vector_stores", tags=["vector_stores"])
    server_router.include_router(user_feedback_router, prefix="/user_feedback", tags=["user_feedback"])
    server_router.include_router(connectors_router, prefix="/connectors", tags=["connectors"])

    well_known_router = APIRouter()
    well_known_router.include_router(auth_well_known_router, prefix="")

    app.include_router(server_router, prefix="/api/v1", tags=["provider"])
    app.include_router(well_known_router, prefix="/.well-known", tags=["well-known"])

    @app.get("/api/v1/openapi.json", include_in_schema=False)
    async def custom_openapi(request: Request):
        openapi_schema = get_openapi(
            title="Agentstack server",
            version=get_version(),
            routes=app.routes,
        )

        base_url = str(request.base_url)
        openapi_schema["servers"] = [{"url": base_url}]

        return JSONResponse(openapi_schema)

    @app.get("/api/v1/docs", include_in_schema=False)
    async def custom_docs(request: Request):
        openapi_url = request.url_for(custom_openapi.__name__)

        return get_swagger_ui_html(
            openapi_url=openapi_url,
            title="BeeAI Platform API Docs",
        )

    @app.get("/healthcheck")
    async def healthcheck():
        return "OK"


def register_telemetry():
    meter = get_meter(INSTRUMENTATION_NAME)

    def scrape_platform_status(options: CallbackOptions) -> Iterable[Observation]:
        yield Observation(value=1)

    meter.create_observable_gauge("platform_status", callbacks=[scrape_platform_status])

    # TODO: extract to a separate "metrics exporter" pod
    # def scrape_providers_by_status(options: CallbackOptions) -> Iterable[Observation]:
    #     providers = provider_container.loaded_providers.values()
    #     for status in ProviderStatus:
    #         count = 0
    #         for provider in providers:
    #             if provider.state == status:
    #                 count += 1
    #         yield Observation(
    #             value=count,
    #             attributes={
    #                 "status": status,
    #             },
    #         )

    # meter.create_observable_gauge("providers_by_status", callbacks=[scrape_providers_by_status])


def app(*, dependency_overrides: Container | None = None, enable_workers: bool = True) -> FastAPI:
    """Entrypoint for API application, called by Uvicorn"""

    logger.info("Bootstrapping dependencies...")
    bootstrap_dependencies_sync(dependency_overrides=dependency_overrides)
    configuration = di[Configuration]

    @asynccontextmanager
    @inject
    async def lifespan(_app: FastAPI, procrastinate_app: procrastinate.App, user_feedback: UserFeedbackService):
        try:
            register_telemetry()
            async with (
                procrastinate_app.open_async(),
                user_feedback,
                run_workers(app=procrastinate_app) if enable_workers else nullcontext(),
            ):
                # Force initial synchronization job
                with suppress(AlreadyEnqueued):
                    await check_registry.defer_async(timestamp=int(time.time()))
                with suppress(AlreadyEnqueued):
                    await check_model_provider_registry.defer_async(timestamp=int(time.time()))
                with suppress(AlreadyEnqueued):
                    await update_model_state_and_cache.defer_async(timestamp=int(time.time()))
                try:
                    yield
                finally:
                    shutdown_telemetry()
        except Exception as e:
            logger.error("Error during startup: %s", repr(extract_messages(e)))
            raise

    app = FastAPI(
        lifespan=lifespan,
        default_response_class=ORJSONResponse,  # better performance then default + handle NaN floats
        docs_url=None,
        openapi_url=None,
        servers=None,
    )

    logger.info("Mounting routes...")
    mount_routes(app)

    # Execution order is important here: https://fastapi.tiangolo.com/tutorial/middleware/#multiple-middleware-execution-order
    if configuration.cors.enabled:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=configuration.cors.allow_origins,
            allow_credentials=configuration.cors.allow_credentials,
            allow_methods=configuration.cors.allow_methods,
            allow_headers=configuration.cors.allow_headers,
        )
    app.add_middleware(RateLimitMiddleware, limiter_storage=di[Storage], configuration=configuration.rate_limit)
    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*" if configuration.trust_proxy_headers else "")

    register_global_exception_handlers(app)
    return app
