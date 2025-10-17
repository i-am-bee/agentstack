# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated
from urllib.parse import urljoin
from uuid import UUID

import fastapi
import fastapi.responses
from a2a.server.apps import A2AFastAPIApplication
from a2a.server.apps.rest.rest_adapter import RESTAdapter
from a2a.types import AgentCard, AgentInterface, TransportProtocol
from a2a.utils import AGENT_CARD_WELL_KNOWN_PATH
from fastapi import Depends, HTTPException, Request

from beeai_server.api.dependencies import (
    A2AProxyServiceDependency,
    ProviderServiceDependency,
    RequiresPermissions,
)
from beeai_server.domain.models.permissions import AuthorizedUser
from beeai_server.service_layer.services.a2a import A2AServerResponse

_SUPPORTED_TRANSPORTS = [TransportProtocol.http_json]


router = fastapi.APIRouter()


def create_proxy_agent_card(agent_card: AgentCard, *, provider_id: UUID, request: Request) -> AgentCard:
    proxy_base = str(request.url_for(a2a_proxy_jsonrpc_transport.__name__, provider_id=provider_id))
    return agent_card.model_copy(
        update={
            "preferred_transport": TransportProtocol.jsonrpc,
            "url": proxy_base,
            "additional_interfaces": [
                AgentInterface(transport=TransportProtocol.http_json, url=urljoin(proxy_base, "http")),
                AgentInterface(transport=TransportProtocol.jsonrpc, url=proxy_base),
            ],
        }
    )


def _to_fastapi(response: A2AServerResponse):
    common = {"status_code": response.status_code, "headers": response.headers, "media_type": response.media_type}
    if response.stream:
        return fastapi.responses.StreamingResponse(content=response.stream, **common)
    else:
        return fastapi.responses.Response(content=response.content, **common)


@router.get("/{provider_id}" + AGENT_CARD_WELL_KNOWN_PATH)
async def get_agent_card(
    provider_id: UUID,
    request: Request,
    provider_service: ProviderServiceDependency,
    _: Annotated[AuthorizedUser, Depends(RequiresPermissions(providers={"read"}))],
) -> AgentCard:
    provider = await provider_service.get_provider(provider_id=provider_id)
    return create_proxy_agent_card(provider.agent_card, provider_id=provider.id, request=request)


@router.post("/{provider_id}")
@router.post("/{provider_id}/")
async def a2a_proxy_jsonrpc_transport(
    provider_id: UUID,
    request: fastapi.requests.Request,
    a2a_proxy: A2AProxyServiceDependency,
    provider_service: ProviderServiceDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(a2a_proxy={"*"}))],
):
    provider = await provider_service.get_provider(provider_id=provider_id)
    agent_card = create_proxy_agent_card(provider.agent_card, provider_id=provider.id, request=request)

    handler = await a2a_proxy.get_request_handler(provider=provider, user=user.user)
    app = A2AFastAPIApplication(agent_card=agent_card, http_handler=handler)
    return await app._handle_requests(request)


@router.api_route("/{provider_id}/http", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
@router.api_route(
    "/{provider_id}/http/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
)
async def a2a_proxy_http_transport(
    provider_id: UUID,
    request: fastapi.requests.Request,
    a2a_proxy: A2AProxyServiceDependency,
    provider_service: ProviderServiceDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(a2a_proxy={"*"}))],
    path: str = "",
):
    provider = await provider_service.get_provider(provider_id=provider_id)
    agent_card = create_proxy_agent_card(provider.agent_card, provider_id=provider.id, request=request)

    handler = await a2a_proxy.get_request_handler(provider=provider, user=user.user)
    adapter = RESTAdapter(agent_card=agent_card, http_handler=handler)

    if not (handler := adapter.routes().get((f"/{path.rstrip('/')}", request.method), None)):
        raise HTTPException(status_code=404, detail="Not found")

    return await handler(request)


# TODO: extra a2a routes are not supported
