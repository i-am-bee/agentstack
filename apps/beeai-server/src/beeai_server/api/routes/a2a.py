# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from uuid import UUID

import fastapi
import fastapi.responses
from a2a.types import AgentCard
from fastapi import Request

from beeai_server.api.dependencies import (
    A2AProxyServiceDependency,
    AuthenticatedUserDependency,
    ProviderServiceDependency,
)
from beeai_server.service_layer.services.a2a import A2AServerResponse

router = fastapi.APIRouter()


def _to_fastapi(response: A2AServerResponse):
    common = {"status_code": response.status_code, "headers": response.headers, "media_type": response.media_type}
    if response.stream:
        return fastapi.responses.StreamingResponse(content=response.stream, **common)
    else:
        return fastapi.responses.Response(content=response.content, **common)


@router.api_route("/{provider_id}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def proxy_request(
    provider_id: UUID,
    request: fastapi.requests.Request,
    a2a_proxy: A2AProxyServiceDependency,
    _: AuthenticatedUserDependency,
    path: str = "",
):
    client = await a2a_proxy.get_proxy_client(provider_id=provider_id)
    response = await client.send_request(method=request.method, url=f"/{path}", content=request.stream())
    return _to_fastapi(response)


@router.get("/{provider_id}/.well-known/agent.json")
async def get_agent_card(
    provider_id: UUID, request: Request, provider_service: ProviderServiceDependency, _: AuthenticatedUserDependency
) -> AgentCard:
    provider = await provider_service.get_provider(provider_id=provider_id)
    url = str(request.url_for(proxy_request.__name__, provider_id=provider.id, path=""))
    return provider.agent_card.model_copy(update={"url": url}).model_dump(exclude_none=True, by_alias=True)
