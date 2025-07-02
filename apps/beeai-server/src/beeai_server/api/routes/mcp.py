# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import fastapi

from beeai_server.api.dependencies import AdminUserDependency, AuthenticatedUserDependency, McpServiceDependency
from beeai_server.api.schema.mcp import CreateMcpProviderRequest, CreateToolkitRequest, McpProvider, Tool, Toolkit
from beeai_server.api.utils import to_fastapi

router = fastapi.APIRouter()


@router.post("/providers", response_model=McpProvider)
async def create_provider(
    request: CreateMcpProviderRequest,
    mcp_service: McpServiceDependency,
    _: AdminUserDependency,
):
    provider = await mcp_service.create_provider(
        name=request.name, location=request.location, transport=request.transport
    )
    return provider


@router.get("/providers", response_model=list[McpProvider])
async def list_providers(mcp_service: McpServiceDependency, _: AdminUserDependency):
    providers = await mcp_service.list_providers()
    return providers


@router.get("/providers/{provider_id}", response_model=McpProvider)
async def read_provider(provider_id: str, mcp_service: McpServiceDependency, _: AdminUserDependency):
    provider = await mcp_service.read_provider(provider_id=provider_id)
    return provider


@router.delete("/providers/{provider_id}", status_code=fastapi.status.HTTP_204_NO_CONTENT)
async def delete_provider(provider_id: str, mcp_service: McpServiceDependency, _: AdminUserDependency):
    await mcp_service.delete_provider(provider_id=provider_id)


@router.get("/tools", response_model=list[Tool])
async def list_tools(mcp_service: McpServiceDependency, user: AuthenticatedUserDependency):
    tools = await mcp_service.list_tools()
    return tools


@router.get("/tools/{tool_id}", response_model=Tool)
async def read_tool(tool_id: str, mcp_service: McpServiceDependency, user: AuthenticatedUserDependency):
    tool = await mcp_service.read_tool(tool_id=tool_id)
    return tool


@router.post("/toolkits", response_model=Toolkit)
async def create_toolkit(
    request: CreateToolkitRequest, mcp_service: McpServiceDependency, user: AuthenticatedUserDependency
):
    toolkit = await mcp_service.create_toolkit(tools=request.tools)
    return toolkit


@router.post("/toolkits/{toolkit_id}/mcp")
@router.get("/toolkits/{toolkit_id}/mcp")
async def mcp_toolkit(
    toolkit_id: str, request: fastapi.Request, mcp_service: McpServiceDependency, user: AuthenticatedUserDependency
) -> None:
    # TODO Redirect to Forge once it supports spec auth
    response = await mcp_service.streamable_http_proxy(request, toolkit_id=toolkit_id)
    return to_fastapi(response)


@router.post("")
@router.get("")
async def mcp(request: fastapi.Request, mcp_service: McpServiceDependency, _: AdminUserDependency) -> None:
    # TODO Redirect to Forge once it supports spec auth
    response = await mcp_service.streamable_http_proxy(request, toolkit_id=None)
    return to_fastapi(response)
