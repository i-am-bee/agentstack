# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated
from urllib.parse import urljoin, urlparse
from uuid import UUID

import fastapi
import fastapi.responses
from a2a.types import AgentCard, TransportProtocol
from a2a.utils import AGENT_CARD_WELL_KNOWN_PATH
from fastapi import Depends, Request

from beeai_server.api.dependencies import (
    A2AProxyServiceDependency,
    ProviderServiceDependency,
    RequiresPermissions,
)
from beeai_server.domain.models.permissions import AuthorizedUser
from beeai_server.service_layer.services.a2a import A2AServerResponse

_SUPPORTED_TRANSPORTS = [TransportProtocol.jsonrpc, TransportProtocol.http_json]


router = fastapi.APIRouter()


def _create_proxy_url(url: str, *, proxy_base: str) -> str:
    return urljoin(proxy_base, urlparse(url).path.lstrip("/"))


def create_proxy_agent_card(agent_card: AgentCard, *, provider_id, request: Request) -> AgentCard:
    proxy_base = str(request.url_for(proxy_request.__name__, provider_id=provider_id, path=""))
    proxy_interfaces = (
        [
            interface.model_copy(update={"url": _create_proxy_url(interface.url, proxy_base=proxy_base)})
            for interface in agent_card.additional_interfaces
            if interface.transport in _SUPPORTED_TRANSPORTS
        ]
        if agent_card.additional_interfaces
        else None
    )
    if agent_card.preferred_transport in _SUPPORTED_TRANSPORTS:
        return agent_card.model_copy(
            update={
                "url": _create_proxy_url(agent_card.url, proxy_base=proxy_base),
                "additional_interfaces": proxy_interfaces,
            }
        )
    elif proxy_interfaces:
        interface = proxy_interfaces[0]
        return agent_card.model_copy(
            update={
                "url": interface.url,
                "preferred_transport": interface.transport,
                "additional_interfaces": proxy_interfaces,
            }
        )
    else:
        raise RuntimeError("Provider doesn't have any transport supported by the proxy.")


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


@router.api_route("/{provider_id}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
@router.api_route("/{provider_id}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def proxy_request(
    provider_id: UUID,
    request: fastapi.requests.Request,
    a2a_proxy: A2AProxyServiceDependency,
    _: Annotated[AuthorizedUser, Depends(RequiresPermissions(a2a_proxy={"*"}))],
    path: str = "",
):
    client = await a2a_proxy.get_proxy_client(provider_id=provider_id)
    response = await client.send_request(method=request.method, url=f"/{path}", content=request.stream())
    return _to_fastapi(response)
