# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from agentstack_server.api.dependencies import (
    ConnectorServiceDependency,
    RequiresPermissions,
)
from agentstack_server.api.schema.connector import (
    AuthorizationCodeRequest,
    ConnectorConnectRequest,
    ConnectorCreateRequest,
    ConnectorResponse,
)
from agentstack_server.domain.models.common import PaginatedResult
from agentstack_server.domain.models.connector import Connector
from agentstack_server.domain.models.permissions import AuthorizedUser

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_connector(
    request: ConnectorCreateRequest,
    connector_service: ConnectorServiceDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(connectors={"write"}))],
) -> ConnectorResponse:
    return _to_response(
        await connector_service.create_connector(
            user=user.user,
            url=request.url,
            client_id=request.client_id,
            client_secret=request.client_secret,
            metadata=request.metadata,
        )
    )


@router.get("/{connector_id}")
async def read_connector(
    connector_id: UUID,
    connector_service: ConnectorServiceDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(connectors={"read"}))],
) -> ConnectorResponse:
    return _to_response(await connector_service.read_connector(connector_id=connector_id, user=user.user))


@router.delete("/{connector_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connector(
    connector_id: UUID,
    connector_service: ConnectorServiceDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(connectors={"write"}))],
) -> None:
    return await connector_service.delete_connector(connector_id=connector_id, user=user.user)


@router.get("")
async def list_connectors(
    connector_service: ConnectorServiceDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(connectors={"read"}))],
) -> PaginatedResult[ConnectorResponse]:
    connectors = await connector_service.list_connectors(user=user.user)
    return PaginatedResult(items=[_to_response(connector) for connector in connectors], total_count=len(connectors))


@router.post("/{connector_id}/connect")
async def connect_connector(
    connector_id: UUID,
    connector_service: ConnectorServiceDependency,
    connect_request: ConnectorConnectRequest,
    request: Request,
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(connectors={"write"}))],
) -> ConnectorResponse:
    return _to_response(
        await connector_service.connect_connector(
            connector_id=connector_id,
            user=user.user,
            redirect_url=connect_request.redirect_url,
            callback_uri=str(request.url_for(oauth_callback.__name__)),
        )
    )


@router.post("/{connector_id}/disconnect")
async def disconnect_connector(
    connector_id: UUID,
    connector_service: ConnectorServiceDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(connectors={"write"}))],
) -> ConnectorResponse:
    return _to_response(await connector_service.disconnect_connector(connector_id=connector_id, user=user.user))


@router.get("/oauth/callback")
async def oauth_callback(
    request: Request,
    state: str,
    connector_service: ConnectorServiceDependency,
    error: str | None = None,
    error_description: str | None = None,
):
    return await connector_service.oauth_callback(
        callback_url=str(request.url), state=state, error=error, error_description=error_description
    )


def _to_response(connector: Connector) -> ConnectorResponse:
    def get_auth_request():
        if not connector.auth or not connector.auth.flow:
            return None
        match connector.auth.flow.type:
            case "code":
                return AuthorizationCodeRequest(authorization_endpoint=connector.auth.flow.authorization_endpoint)

    return ConnectorResponse(
        id=connector.id,
        url=connector.url,
        state=connector.state,
        auth_request=get_auth_request(),
        disconnect_reason=connector.disconnect_reason,
        metadata=connector.metadata,
    )
