# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from uuid import UUID

import fastapi
import fastapi.responses
from a2a.types import AgentCard

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


@router.post("/{provider_id}")
async def send_request(
    provider_id: UUID,
    request: fastapi.requests.Request,
    a2a_proxy: A2AProxyServiceDependency,
    _: AuthenticatedUserDependency,
):
    client = await a2a_proxy.get_proxy_client(provider_id=provider_id)
    response = await a2a_proxy.send_request(client=client, method=request.method, url="/", json=await request.json())
    return _to_fastapi(response)


@router.get("/{provider_id}/.well-known/agent.json")
async def get_agent_card(
    provider_id: UUID, provider_service: ProviderServiceDependency, _: AuthenticatedUserDependency
) -> AgentCard:
    provider = await provider_service.get_provider(provider_id=provider_id)
    return provider.agent_card.model_dump(exclude_none=True, by_alias=True)
