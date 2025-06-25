# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import fastapi
import fastapi.responses
from acp_sdk import PingResponse, SessionId, SessionReadResponse
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
    context = await acp_service.get_proxy_context(agent_name=request.agent_name, user=user)
    response = await acp_service.send_request(context, "POST", "/runs", request)
    return _to_fastapi(response)


@router.get("/runs/{run_id}")
async def read_run(
    run_id: RunId, acp_service: AcpProxyServiceDependency, user: AuthenticatedUserDependency
) -> RunReadResponse:
    client = await acp_service.get_proxy_context(run_id=run_id, user=user)
    response = await acp_service.send_request(client, "GET", f"/runs/{run_id}")
    return _to_fastapi(response)


@router.get("/runs/{run_id}/events")
async def read_run_events(
    run_id: RunId, acp_service: AcpProxyServiceDependency, user: AuthenticatedUserDependency
) -> RunReadResponse:
    client = await acp_service.get_proxy_context(run_id=run_id, user=user)
    response = await acp_service.send_request(client, "GET", f"/runs/{run_id}/events")
    return _to_fastapi(response)


@router.post("/runs/{run_id}")
async def resume_run(
    run_id: RunId, request: RunResumeRequest, acp_service: AcpProxyServiceDependency, user: AuthenticatedUserDependency
) -> RunResumeResponse:
    client = await acp_service.get_proxy_context(run_id=run_id, user=user)
    response = await acp_service.send_request(client, "POST", f"/runs/{run_id}", request)
    return _to_fastapi(response)


@router.post("/runs/{run_id}/cancel")
async def cancel_run(
    run_id: RunId, acp_service: AcpProxyServiceDependency, user: AuthenticatedUserDependency
) -> RunCancelResponse:
    client = await acp_service.get_proxy_context(run_id=run_id, user=user)
    response = await acp_service.send_request(client, "POST", f"/runs/{run_id}/cancel")
    return _to_fastapi(response)


@router.get("/sessions/{session_id}")
async def read_session(
    session_id: SessionId, acp_service: AcpProxyServiceDependency, user: AuthenticatedUserDependency
) -> SessionReadResponse:
    client = await acp_service.get_proxy_context(session_id=session_id, user=user)
    response = await acp_service.send_request(client, "GET", f"/sessions/{session_id}")
    return _to_fastapi(response)
