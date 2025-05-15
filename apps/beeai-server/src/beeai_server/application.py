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
import pathlib
from contextlib import asynccontextmanager
from typing import Iterable

from acp_sdk import ACPError
from acp_sdk.server.errors import (
    acp_error_handler,
    validation_exception_handler,
    catch_all_exception_handler,
    http_exception_handler as acp_http_exception_handler,
)
from starlette.requests import Request

from beeai_server.utils.fastapi import NoCacheStaticFiles
from fastapi import FastAPI, APIRouter
from fastapi import HTTPException
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import ORJSONResponse
from kink import inject, di
from starlette.responses import FileResponse
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_400_BAD_REQUEST
from starlette.exceptions import HTTPException as StarletteHttpException
from opentelemetry.metrics import get_meter, Observation, CallbackOptions
from fastapi.exceptions import RequestValidationError

from beeai_server.telemetry import INSTRUMENTATION_NAME, shutdown_telemetry
from beeai_server.bootstrap import bootstrap_dependencies_sync
from beeai_server.configuration import Configuration
from beeai_server.exceptions import ManifestLoadError, ProviderNotInstalledError
from beeai_server.api.routes.provider import router as provider_router
from beeai_server.api.routes.acp import router as acp_router
from beeai_server.api.routes.env import router as env_router
from beeai_server.api.routes.telemetry import router as telemetry_router
from beeai_server.api.routes.llm import router as llm_router
from beeai_server.api.routes.ui import router as ui_router

logger = logging.getLogger(__name__)


def extract_messages(exc):
    if isinstance(exc, BaseExceptionGroup):
        return [(exc_type, msg) for e in exc.exceptions for exc_type, msg in extract_messages(e)]
    else:
        return [(type(exc).__name__, str(exc))]


def register_global_exception_handlers(app: FastAPI):
    @app.exception_handler(ManifestLoadError)
    async def entity_not_found_exception_handler(request, exc: ManifestLoadError):
        return await http_exception_handler(request, HTTPException(status_code=exc.status_code, detail=str(exc)))

    @app.exception_handler(Exception)
    @app.exception_handler(HTTPException)
    async def custom_http_exception_handler(request: Request, exc):
        """Include detail in all unhandled exceptions.

        This is not the beset security practice as it can reveal details about the internal workings of this service,
        but this is an open-source service anyway, so the risk is acceptable
        """

        if request.url.path.startswith("/api/v1/acp"):
            match exc:
                case ACPError():
                    return await acp_error_handler(request, exc)
                case StarletteHttpException():
                    return await acp_http_exception_handler(request, exc)
                case RequestValidationError():
                    return await validation_exception_handler(request, exc)
                case ProviderNotInstalledError():
                    return await acp_http_exception_handler(
                        request, HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(exc))
                    )
                case _:
                    return await catch_all_exception_handler(request, exc)

        logger.error("Error during HTTP request: %s", repr(extract_messages(exc)))

        match exc:
            case HTTPException():
                exception = exc
            case _:
                exception = HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, detail=repr(extract_messages(exc)))
        return await http_exception_handler(request, exception)


def mount_routes(app: FastAPI):
    static_directory = pathlib.Path(__file__).parent.joinpath("static")
    if not static_directory.joinpath("index.html").exists():  # this check is for running locally
        raise RuntimeError("Could not find static files -- ensure that beeai-ui is built: `mise build:beeai-ui`")

    ui_app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    ui_app.mount("/", NoCacheStaticFiles(directory=static_directory, html=True))
    ui_app.add_exception_handler(
        404,
        lambda _req, _exc: FileResponse(
            static_directory / "index.html",
            status_code=200,
            headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"},
        ),
    )

    server_router = APIRouter()
    server_router.include_router(acp_router, prefix="/acp")
    server_router.include_router(provider_router, prefix="/providers", tags=["providers"])
    server_router.include_router(env_router, prefix="/variables", tags=["variables"])
    server_router.include_router(telemetry_router, prefix="/telemetry", tags=["telemetry"])
    server_router.include_router(llm_router, prefix="/llm", tags=["llm"])
    server_router.include_router(ui_router, prefix="/ui", tags=["ui"])

    app.mount("/healthcheck", lambda: "OK")
    app.include_router(server_router, prefix="/api/v1", tags=["provider"])
    app.mount("/", ui_app)


def register_telemetry():
    meter = get_meter(INSTRUMENTATION_NAME)

    def scrape_platform_status(options: CallbackOptions) -> Iterable[Observation]:
        yield Observation(value=1)

    meter.create_observable_gauge("platform_status", callbacks=[scrape_platform_status])

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


@asynccontextmanager
@inject
async def lifespan(_app: FastAPI):
    from beeai_server.utils.periodic import run_all_crons

    async with run_all_crons():
        try:
            yield
        finally:
            shutdown_telemetry()


def app() -> FastAPI:
    """Entrypoint for API application, called by Uvicorn"""

    logger.info("Bootstrapping dependencies...")
    bootstrap_dependencies_sync()
    configuration = di[Configuration]

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
