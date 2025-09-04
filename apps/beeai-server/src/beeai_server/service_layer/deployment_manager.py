# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from datetime import timedelta
from typing import Protocol
from uuid import UUID

from kink import inject
from pydantic import HttpUrl

from beeai_server.configuration import Configuration
from beeai_server.domain.models.provider import Provider, ProviderDeploymentState
from beeai_server.utils.logs_container import LogsContainer


@inject
def global_provider_variables(configuration: Configuration):
    return {
        "PORT": "8000",
        "HOST": "0.0.0.0",
        "OTEL_EXPORTER_OTLP_ENDPOINT": str(configuration.telemetry.collector_url),
        "PLATFORM_URL": f"http://{configuration.platform_service_url}",
    }


class IProviderDeploymentManager(Protocol):
    async def create_or_replace(self, *, provider: Provider, env: dict[str, str] | None = None) -> bool: ...
    async def delete(self, *, provider_id: UUID) -> None: ...
    async def state(self, *, provider_ids: list[UUID]) -> list[ProviderDeploymentState]: ...
    async def scale_down(self, *, provider_id: UUID) -> None: ...
    async def scale_up(self, *, provider_id: UUID) -> None: ...
    async def wait_for_startup(self, *, provider_id: UUID, timeout: timedelta) -> None: ...  # noqa: ASYNC109 (the timeout actually corresponds to kubernetes timeout)
    async def get_provider_url(self, *, provider_id: UUID) -> HttpUrl: ...
    async def stream_logs(self, *, provider_id: UUID, logs_container: LogsContainer) -> None: ...
