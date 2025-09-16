# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import logging

from fastapi import APIRouter

from beeai_server.api.dependencies import AuthServiceDependency

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/.well-known/oauth-protected-resource")
def protected_resource_metadata(auth_servide: AuthServiceDependency):
    return auth_servide.protected_resource_metadata()
