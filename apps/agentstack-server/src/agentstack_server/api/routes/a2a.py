# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Annotated, Any
from urllib.parse import urljoin
from uuid import UUID

import fastapi
from a2a.server.apps import A2AFastAPIApplication
from a2a.server.apps.rest.rest_adapter import RESTAdapter
from a2a.types import AgentCard, AgentInterface, HTTPAuthSecurityScheme, SecurityRequirement, SecurityScheme
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH
from fastapi import Depends, HTTPException, Request, Response
from google.protobuf.json_format import MessageToDict, ParseDict

from agentstack_server.api.dependencies import (
    A2AProxyServiceDependency,
    ConfigurationDependency,
    ProviderServiceDependency,
    RequiresPermissions,
    authorized_user,
)
from agentstack_server.configuration import Configuration
from agentstack_server.domain.models.permissions import AuthorizedUser

router = fastapi.APIRouter()


def create_proxy_agent_card(
    agent_card: dict[str, Any], *, provider_id: UUID, request: Request, configuration: Configuration
) -> AgentCard:
    proxy_base = str(request.url_for(a2a_proxy_jsonrpc_transport.__name__, provider_id=provider_id))
    proxy_security_schemes = {
        "platform_context_token": SecurityScheme(
            http_auth_security_scheme=HTTPAuthSecurityScheme(
                scheme="bearer",
                bearer_format="JWT",
                description="Platform context token, issued by the AgentStack server using POST /api/v1/context/{context_id}/token.",
            )
        )
    }

    proxy_security = []

    if not configuration.auth.disable_auth:
        # Note that we're purposefully not using oAuth but a more generic http scheme.
        # This is because we don't want to declare the auth metadata but prefer discovery through related RFCs
        # The http scheme also covers internal jwt tokens
        req = SecurityRequirement()
        req.schemes["bearer"].list.extend([])
        proxy_security.append(req)
        proxy_security_schemes["bearer"] = SecurityScheme(
            http_auth_security_scheme=HTTPAuthSecurityScheme(scheme="bearer")
        )
        if configuration.auth.basic.enabled:
            req_basic = SecurityRequirement()
            req_basic.schemes["basic"].list.extend([])
            proxy_security.append(req_basic)
            proxy_security_schemes["basic"] = SecurityScheme(
                http_auth_security_scheme=HTTPAuthSecurityScheme(scheme="basic")
            )

    card_copy = AgentCard()
    card_copy = ParseDict(agent_card, card_copy, ignore_unknown_fields=True)

    del card_copy.supported_interfaces[:]
    card_copy.supported_interfaces.extend(
        [
            AgentInterface(protocol_binding="HTTP+JSON", url=urljoin(proxy_base, "http")),
            AgentInterface(protocol_binding="JSONRPC", url=proxy_base),
        ]
    )

    del card_copy.security_requirements[:]
    card_copy.security_requirements.extend(proxy_security)

    card_copy.security_schemes.clear()
    for k, v in proxy_security_schemes.items():
        card_copy.security_schemes[k].CopyFrom(v)

    return card_copy


@router.get("/{provider_id}" + AGENT_CARD_WELL_KNOWN_PATH)
async def get_agent_card(
    provider_id: UUID,
    request: Request,
    provider_service: ProviderServiceDependency,
    configuration: ConfigurationDependency,
    user: Annotated[AuthorizedUser, Depends(authorized_user)],
) -> dict[str, Any]:
    try:
        user = RequiresPermissions(providers={"read"})(user)  # try provider read permissions
    except HTTPException:
        user = RequiresPermissions(a2a_proxy={provider_id})(user)  # try a2a proxy permissions

    provider = await provider_service.get_provider(provider_id=provider_id)
    card_copy = create_proxy_agent_card(
        provider.agent_card, provider_id=provider.id, request=request, configuration=configuration
    )
    return MessageToDict(card_copy, preserving_proto_field_name=True)


@router.post("/{provider_id}")
@router.post("/{provider_id}/")
async def a2a_proxy_jsonrpc_transport(
    provider_id: UUID,
    request: fastapi.requests.Request,
    a2a_proxy: A2AProxyServiceDependency,
    provider_service: ProviderServiceDependency,
    configuration: ConfigurationDependency,
    user: Annotated[AuthorizedUser, Depends(authorized_user)],
) -> Response:
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
) -> Response:
    provider = await provider_service.get_provider(provider_id=provider_id)
    handler = (
        RESTAdapter(
            agent_card=create_proxy_agent_card(
                provider.agent_card, provider_id=provider.id, request=request, configuration=configuration
            ),
            http_handler=await a2a_proxy.get_request_handler(
                provider=provider, user=RequiresPermissions(a2a_proxy={provider_id})(user).user
            ),
        )
        .routes()
        .get((f"/{path.rstrip('/')}", request.method), None)
    )
    if not handler:
        raise HTTPException(status_code=404, detail="Not found")
    return await handler(request)


# TODO: extra a2a routes are not supported
