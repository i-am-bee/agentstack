# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
import time
from collections.abc import Iterable
from contextlib import asynccontextmanager, suppress

import procrastinate
from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import ORJSONResponse
from kink import Container, di, inject
from opentelemetry.metrics import CallbackOptions, Observation, get_meter
from procrastinate.exceptions import AlreadyEnqueued
from starlette.requests import Request
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_500_INTERNAL_SERVER_ERROR

from beeai_server.api.routes.a2a import router as a2a_router
from beeai_server.api.routes.auth import well_known_router as auth_well_known_router
from beeai_server.api.routes.configurations import router as configuration_router
from beeai_server.api.routes.connectors import router as connectors_router
from beeai_server.api.routes.contexts import router as contexts_router
from beeai_server.api.routes.files import router as files_router
from beeai_server.api.routes.mcp import router as mcp_router
from beeai_server.api.routes.model_providers import router as model_providers_router
from beeai_server.api.routes.openai import router as openai_router
from beeai_server.api.routes.provider_builds import router as provider_builds_router
from beeai_server.api.routes.providers import router as provider_router
from beeai_server.api.routes.user_feedback import router as user_feedback_router
from beeai_server.api.routes.variables import router as variables_router
from beeai_server.api.routes.vector_stores import router as vector_stores_router
from beeai_server.bootstrap import bootstrap_dependencies_sync
from beeai_server.configuration import Configuration
from beeai_server.exceptions import (
    DuplicateEntityError,
    ManifestLoadError,
    PlatformError,
)
from beeai_server.jobs.crons.provider import check_registry
from beeai_server.run_workers import run_workers
from beeai_server.service_layer.services.mcp import McpService
from beeai_server.telemetry import INSTRUMENTATION_NAME, shutdown_telemetry
from beeai_server.utils.fastapi import ProxyHeadersMiddleware

logger = logging.getLogger(__name__)


def extract_messages(exc):
    if isinstance(exc, BaseExceptionGroup):
        return [(exc_type, msg) for e in exc.exceptions for exc_type, msg in extract_messages(e)]
    else:
        return [(type(exc).__name__, str(exc))]


def register_global_exception_handlers(app: FastAPI):
    @app.exception_handler(PlatformError)
    async def entity_not_found_exception_handler(request, exc: ManifestLoadError | DuplicateEntityError):
        return await http_exception_handler(request, HTTPException(status_code=exc.status_code, detail=str(exc)))

    @app.exception_handler(Exception)
    @app.exception_handler(HTTPException)
    async def custom_http_exception_handler(request: Request, exc):
        """Include detail in all unhandled exceptions.

        This is not the beset security practice as it can reveal details about the internal workings of this service,
        but this is an open-source service anyway, so the risk is acceptable
        """

        logger.error("Error during HTTP request: %s", repr(extract_messages(exc)))

        if request.url.path.startswith("/api/v1/a2a"):
            match exc:
                case _:
                    ...  # TODO

        match exc:
            case HTTPException():
                exception = exc
            case _:
                exception = HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, detail=repr(extract_messages(exc)))

        if isinstance(exception, HTTPException) and exc.status_code == HTTP_401_UNAUTHORIZED:
            exception.headers = exception.headers or {}
            exception.headers |= {
                "WWW-Authenticate": f'Bearer resource_metadata="{request.url.replace(path="/.well-known/oauth-protected-resource")}"'  # We don't define multiple resource domains at the moment
            }

        return await http_exception_handler(request, exception)


def mount_routes(app: FastAPI):
    server_router = APIRouter()
    server_router.include_router(a2a_router, prefix="/a2a")
    server_router.include_router(mcp_router, prefix="/mcp")
    server_router.include_router(provider_router, prefix="/providers", tags=["providers"])
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


def app(*, dependency_overrides: Container | None = None) -> FastAPI:
    """Entrypoint for API application, called by Uvicorn"""

    logger.info("Bootstrapping dependencies...")
    bootstrap_dependencies_sync(dependency_overrides=dependency_overrides)
    configuration = di[Configuration]

    @asynccontextmanager
    @inject
    async def lifespan(_app: FastAPI, procrastinate_app: procrastinate.App, mcp_service: McpService):
        try:
            register_telemetry()
            async with procrastinate_app.open_async(), run_workers(app=procrastinate_app), mcp_service:
                with suppress(AlreadyEnqueued):
                    # Force initial sync of the registry immediately
                    await check_registry.defer_async(timestamp=int(time.time()))
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
        docs_url="/api/v1/docs",
        openapi_url="/api/v1/openapi.json",
        servers=[{"url": f"http://localhost:{configuration.port}"}],
    )

    logger.info("Mounting routes...")
    mount_routes(app)

    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*" if configuration.trust_proxy_headers else "")
    register_global_exception_handlers(app)

    return app
