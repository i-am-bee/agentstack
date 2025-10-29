# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import logging

from fastapi import APIRouter, Request

from agentstack_server.api.auth.utils import create_resource_uri
from agentstack_server.api.dependencies import AuthServiceDependency

logger = logging.getLogger(__name__)

well_known_router = APIRouter()


@well_known_router.get("/oauth-protected-resource/{resource:path}")
def protected_resource_metadata(
    request: Request,
    auth_service: AuthServiceDependency,
    resource: str = "",
):
    return auth_service.protected_resource_metadata(resource=create_resource_uri(request.url.replace(path=resource)))
