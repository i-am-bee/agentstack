# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated

import fastapi
from fastapi import Depends

from agentstack_server.api.dependencies import McpServiceDependency, RequiresPermissions
from agentstack_server.api.schema.mcp import CreateMcpProviderRequest, CreateToolkitRequest, McpProvider, Tool, Toolkit
from agentstack_server.api.utils import to_fastapi
from agentstack_server.domain.models.permissions import AuthorizedUser

router = fastapi.APIRouter()


@router.post("/providers")
async def create_provider(
    request: CreateMcpProviderRequest,
    mcp_service: McpServiceDependency,
    _: Annotated[AuthorizedUser, Depends(RequiresPermissions(mcp_providers={"write"}))],
) -> McpProvider:
    return await mcp_service.create_provider(name=request.name, location=request.location, transport=request.transport)


@router.get("/providers")
async def list_providers(
    mcp_service: McpServiceDependency,
    _: Annotated[AuthorizedUser, Depends(RequiresPermissions(mcp_providers={"read"}))],
) -> list[McpProvider]:
    return await mcp_service.list_providers()


@router.get("/providers/{provider_id}")
async def read_provider(
    provider_id: str,
    mcp_service: McpServiceDependency,
    _: Annotated[AuthorizedUser, Depends(RequiresPermissions(mcp_providers={"read"}))],
) -> McpProvider:
    return await mcp_service.read_provider(provider_id=provider_id)


@router.delete("/providers/{provider_id}", status_code=fastapi.status.HTTP_204_NO_CONTENT)
async def delete_provider(
    provider_id: str,
    mcp_service: McpServiceDependency,
    _: Annotated[AuthorizedUser, Depends(RequiresPermissions(mcp_providers={"write"}))],
) -> None:
    await mcp_service.delete_provider(provider_id=provider_id)


@router.get("/tools")
async def list_tools(
    mcp_service: McpServiceDependency,
    _: Annotated[AuthorizedUser, Depends(RequiresPermissions(mcp_tools={"read"}))],
) -> list[Tool]:
    return await mcp_service.list_tools()


@router.get("/tools/{tool_id}")
async def read_tool(
    tool_id: str,
    mcp_service: McpServiceDependency,
    _: Annotated[AuthorizedUser, Depends(RequiresPermissions(mcp_tools={"read"}))],
) -> Tool:
    return await mcp_service.read_tool(tool_id=tool_id)


@router.post("/toolkits")
async def create_toolkit(
    request: CreateToolkitRequest,
    mcp_service: McpServiceDependency,
    _: Annotated[AuthorizedUser, Depends(RequiresPermissions(mcp_providers={"write"}))],
) -> Toolkit:
    return await mcp_service.create_toolkit(tools=request.tools)


@router.post("/toolkits/{toolkit_id}/mcp")
@router.get("/toolkits/{toolkit_id}/mcp")
async def mcp_toolkit(
    toolkit_id: str,
    request: fastapi.Request,
    mcp_service: McpServiceDependency,
    _: Annotated[AuthorizedUser, Depends(RequiresPermissions(mcp_proxy={"*"}))],
):
    # TODO Redirect to Forge once it supports spec auth
    response = await mcp_service.streamable_http_proxy(request, toolkit_id=toolkit_id)
    return to_fastapi(response)


@router.post("")
@router.get("")
async def mcp(
    request: fastapi.Request,
    mcp_service: McpServiceDependency,
    _: Annotated[AuthorizedUser, Depends(RequiresPermissions(mcp_proxy={"*"}))],
):
    # TODO Redirect to Forge once it supports spec auth
    response = await mcp_service.streamable_http_proxy(request, toolkit_id=None)
    return to_fastapi(response)
