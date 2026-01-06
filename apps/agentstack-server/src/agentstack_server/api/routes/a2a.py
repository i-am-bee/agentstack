# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated
from urllib.parse import urljoin
from uuid import UUID

import fastapi
import fastapi.responses
from a2a.server.apps import A2AFastAPIApplication
from a2a.server.apps.rest.rest_adapter import RESTAdapter
from a2a.types import AgentCard, AgentInterface, HTTPAuthSecurityScheme, SecurityScheme, TransportProtocol
from a2a.utils import AGENT_CARD_WELL_KNOWN_PATH
from fastapi import Depends, HTTPException, Request

from agentstack_server.api.dependencies import (
    A2AProxyServiceDependency,
    ConfigurationDependency,
    ProviderServiceDependency,
    RequiresPermissions,
    authorized_user,
)
from agentstack_server.configuration import Configuration
from agentstack_server.domain.models.permissions import AuthorizedUser
from agentstack_server.service_layer.services.a2a import A2AServerResponse

router = fastapi.APIRouter()


def create_proxy_agent_card(
    agent_card: AgentCard, *, provider_id: UUID, request: Request, configuration: Configuration
) -> AgentCard:
    proxy_base = str(request.url_for(a2a_proxy_jsonrpc_transport.__name__, provider_id=provider_id))

    proxy_security = []
    proxy_security_schemes = {}
    if not configuration.auth.disable_auth:
        # Note that we're purposefully not using oAuth but a more generic http scheme.
        # This is because we don't want to declare the auth metadata but prefer discovery through related RFCs
        # The http scheme also covers internal jwt tokens
        proxy_security.append({"bearer": []})
        proxy_security_schemes["bearer"] = SecurityScheme(HTTPAuthSecurityScheme(scheme="bearer"))
        if configuration.auth.basic.enabled:
            proxy_security.append({"basic": []})
            proxy_security_schemes["basic"] = SecurityScheme(HTTPAuthSecurityScheme(scheme="basic"))

    return agent_card.model_copy(
        update={
            "preferred_transport": TransportProtocol.jsonrpc,
            "url": proxy_base,
            "additional_interfaces": [
                AgentInterface(transport=TransportProtocol.http_json, url=urljoin(proxy_base, "http")),
                AgentInterface(transport=TransportProtocol.jsonrpc, url=proxy_base),
            ],
            "security": proxy_security,
            "security_schemes": proxy_security_schemes,
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
    configuration: ConfigurationDependency,
    user: Annotated[AuthorizedUser, Depends(authorized_user)],
) -> AgentCard:
    try:
        user = RequiresPermissions(providers={"read"})(user)  # try provider read permissions
    except HTTPException:
        user = RequiresPermissions(a2a_proxy={provider_id})(user)  # try a2a proxy permissions

    provider = await provider_service.get_provider(provider_id=provider_id)
    return create_proxy_agent_card(
        provider.agent_card, provider_id=provider.id, request=request, configuration=configuration
    )


@router.post("/{provider_id}")
@router.post("/{provider_id}/")
async def a2a_proxy_jsonrpc_transport(
    provider_id: UUID,
    request: fastapi.requests.Request,
    a2a_proxy: A2AProxyServiceDependency,
    provider_service: ProviderServiceDependency,
    configuration: ConfigurationDependency,
    user: Annotated[AuthorizedUser, Depends(authorized_user)],
):
    user = RequiresPermissions(a2a_proxy={provider_id})(user)

    provider = await provider_service.get_provider(provider_id=provider_id)
    agent_card = create_proxy_agent_card(
        provider.agent_card, provider_id=provider.id, request=request, configuration=configuration
    )

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
    configuration: ConfigurationDependency,
    user: Annotated[AuthorizedUser, Depends(authorized_user)],
    path: str = "",
):
    user = RequiresPermissions(a2a_proxy={provider_id})(user)
    provider = await provider_service.get_provider(provider_id=provider_id)
    agent_card = create_proxy_agent_card(
        provider.agent_card, provider_id=provider.id, request=request, configuration=configuration
    )

    handler = await a2a_proxy.get_request_handler(provider=provider, user=user.user)
    adapter = RESTAdapter(agent_card=agent_card, http_handler=handler)

    if not (handler := adapter.routes().get((f"/{path.rstrip('/')}", request.method), None)):
        raise HTTPException(status_code=404, detail="Not found")

    return await handler(request)


# TODO: extra a2a routes are not supported
