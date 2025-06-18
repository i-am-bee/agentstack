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
import fastapi.responses
from acp_sdk import PingResponse
from acp_sdk.models import (
    AgentName,
    RunCancelResponse,
    RunCreateRequest,
    RunCreateResponse,
    RunId,
    RunReadResponse,
    RunResumeRequest,
    RunResumeResponse,
)

from beeai_server.api.schema.acp import AgentsListResponse, AgentReadResponse
from beeai_server.api.dependencies import AcpProxyServiceDependency, AuthenticatedUserDependency
from beeai_server.service_layer.services.acp import AcpServerResponse

router = fastapi.APIRouter()


@router.get("/ping")
async def ping() -> PingResponse:
    return PingResponse()


@router.get("/agents")
async def list_agents(acp_service: AcpProxyServiceDependency) -> AgentsListResponse:
    return AgentsListResponse(agents=await acp_service.list_agents())


@router.get("/agents/{name}")
async def read_agent(name: AgentName, acp_service: AcpProxyServiceDependency) -> AgentReadResponse:
    return (await acp_service.get_agent_by_name(name)).model_dump()


def _to_fastapi(response: AcpServerResponse):
    common = {"status_code": response.status_code, "headers": response.headers, "media_type": response.media_type}
    if response.stream:
        return fastapi.responses.StreamingResponse(content=response.stream, **common)
    else:
        return fastapi.responses.Response(content=response.content, **common)


@router.post("/runs")
async def create_run(
    request: RunCreateRequest, acp_service: AcpProxyServiceDependency, user: AuthenticatedUserDependency
) -> RunCreateResponse:
    client = await acp_service.get_proxy_client(agent_name=request.agent_name, user=user)
    response = await acp_service.send_request(client, "POST", "/runs", request)
    return _to_fastapi(response)


@router.get("/runs/{run_id}")
async def read_run(
    run_id: RunId, acp_service: AcpProxyServiceDependency, user: AuthenticatedUserDependency
) -> RunReadResponse:
    client = await acp_service.get_proxy_client(run_id=run_id, user=user)
    response = await acp_service.send_request(client, "GET", f"/runs/{run_id}")
    return _to_fastapi(response)


@router.get("/runs/{run_id}/events")
async def read_run_events(
    run_id: RunId, acp_service: AcpProxyServiceDependency, user: AuthenticatedUserDependency
) -> RunReadResponse:
    client = await acp_service.get_proxy_client(run_id=run_id, user=user)
    response = await acp_service.send_request(client, "GET", f"/runs/{run_id}/events")
    return _to_fastapi(response)


@router.post("/runs/{run_id}")
async def resume_run(
    run_id: RunId, request: RunResumeRequest, acp_service: AcpProxyServiceDependency, user: AuthenticatedUserDependency
) -> RunResumeResponse:
    client = await acp_service.get_proxy_client(run_id=run_id, user=user)
    response = await acp_service.send_request(client, "POST", f"/runs/{run_id}", request)
    return _to_fastapi(response)


@router.post("/runs/{run_id}/cancel")
async def cancel_run(
    run_id: RunId, acp_service: AcpProxyServiceDependency, user: AuthenticatedUserDependency
) -> RunCancelResponse:
    client = await acp_service.get_proxy_client(run_id=run_id, user=user)
    response = await acp_service.send_request(client, "POST", f"/runs/{run_id}/cancel")
    return _to_fastapi(response)
