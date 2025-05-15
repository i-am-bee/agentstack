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

import fastapi

from beeai_server.api.routes.dependencies import TelemetryServiceDependency
from beeai_server.api.schema.telemetry import UpdateTelemetryConfigRequest

router = fastapi.APIRouter()


@router.get("")
async def read_config(telemetry_service: TelemetryServiceDependency):
    return await telemetry_service.read_config()


@router.put("")
async def update_config(request: UpdateTelemetryConfigRequest, telemetry_service: TelemetryServiceDependency):
    await telemetry_service.update_config(sharing_enabled=request.sharing_enabled)
