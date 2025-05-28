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

from datetime import timedelta
from typing import Protocol
from uuid import UUID

from kink import inject
from pydantic import HttpUrl

from beeai_server.configuration import Configuration
from beeai_server.utils.logs_container import LogsContainer
from beeai_server.domain.models.provider import Provider, ProviderDeploymentState


@inject
def global_provider_variables(configuration: Configuration):
    return {
        "PORT": "8000",
        "HOST": "0.0.0.0",
        "OTEL_EXPORTER_OTLP_ENDPOINT": str(configuration.telemetry.collector_url),
        "PLATFORM_URL": f"http://{configuration.platform_service_url}:{configuration.port}",
        "LLM_MODEL": "dummy",
        "LLM_API_KEY": "dummy",
        "LLM_API_BASE": f"http://{configuration.platform_service_url}/api/v1/llm",
    }


class IProviderDeploymentManager(Protocol):
    async def create_or_replace(self, *, provider: Provider, env: dict[str, str] | None = None) -> bool: ...
    async def delete(self, *, provider_id: UUID) -> None: ...
    async def state(self, *, provider_ids: list[UUID]) -> list[ProviderDeploymentState]: ...
    async def scale_down(self, *, provider_id: UUID) -> None: ...
    async def scale_up(self, *, provider_id: UUID) -> None: ...
    async def wait_for_startup(self, *, provider_id: UUID, timeout: timedelta) -> None: ...
    async def get_provider_url(self, *, provider_id: UUID) -> HttpUrl: ...
    async def stream_logs(self, *, provider_id: UUID, logs_container: LogsContainer) -> None: ...
