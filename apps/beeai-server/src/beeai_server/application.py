# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from collections.abc import Iterable
from contextlib import asynccontextmanager

import procrastinate
from acp_sdk import ACPError
from acp_sdk.server.errors import (
    acp_error_handler,
    catch_all_exception_handler,
    validation_exception_handler,
)
from acp_sdk.server.errors import (
    http_exception_handler as acp_http_exception_handler,
)
from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from kink import Container, di, inject
from opentelemetry.metrics import CallbackOptions, Observation, get_meter
from starlette.exceptions import HTTPException as StarletteHttpException
from starlette.requests import Request
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from beeai_server.api.routes.acp import router as acp_router
from beeai_server.api.routes.embeddings import router as embeddings_router
from beeai_server.api.routes.env import router as env_router
from beeai_server.api.routes.files import router as files_router
from beeai_server.api.routes.llm import router as llm_router
from beeai_server.api.routes.provider import router as provider_router
from beeai_server.api.routes.ui import router as ui_router
from beeai_server.api.routes.vector_stores import router as vector_stores_router
from beeai_server.bootstrap import bootstrap_dependencies_sync
from beeai_server.configuration import Configuration
from beeai_server.exceptions import (
    DuplicateEntityError,
    ManifestLoadError,
    PlatformError,
)
from beeai_server.run_workers import run_workers
from beeai_server.telemetry import INSTRUMENTATION_NAME, shutdown_telemetry

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

        if request.url.path.startswith("/api/v1/acp"):
            match exc:
                case ACPError():
                    return await acp_error_handler(request, exc)
                case StarletteHttpException():
                    return await acp_http_exception_handler(request, exc)
                case RequestValidationError():
                    return await validation_exception_handler(request, exc)
                case _:
                    return await catch_all_exception_handler(request, exc)

        match exc:
            case HTTPException():
                exception = exc
            case _:
                exception = HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, detail=repr(extract_messages(exc)))
        return await http_exception_handler(request, exception)


def mount_routes(app: FastAPI):
    server_router = APIRouter()
    server_router.include_router(acp_router, prefix="/acp")
    server_router.include_router(provider_router, prefix="/providers", tags=["providers"])
    server_router.include_router(env_router, prefix="/variables", tags=["variables"])
    server_router.include_router(files_router, prefix="/files", tags=["files"])
    server_router.include_router(llm_router, prefix="/llm", tags=["llm"])
    server_router.include_router(ui_router, prefix="/ui", tags=["ui"])
    server_router.include_router(embeddings_router, prefix="/llm", tags=["embeddings"])
    server_router.include_router(vector_stores_router, prefix="/vector_stores", tags=["vector_stores"])

    app.include_router(server_router, prefix="/api/v1", tags=["provider"])

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
    async def lifespan(_app: FastAPI, procrastinate_app: procrastinate.App):
        try:
            register_telemetry()
            async with procrastinate_app.open_async(), run_workers(app=procrastinate_app):
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
    register_global_exception_handlers(app)
    return app
