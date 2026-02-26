# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
from typing import Any

from kink import inject

from agentstack_server.configuration import Configuration

logger = logging.getLogger(__name__)


@inject
class AuthService:
    def __init__(self, configuration: Configuration):
        self._config = configuration

    def protected_resource_metadata(self, *, resource: str) -> dict[str, Any]:
        if self._config.auth.disable_auth:
            return {"resource": resource, "authorization_servers": [], "client_data": [], "scopes_supported": []}

        provider = self._config.auth.oidc.provider
        return {
            "resource": resource,
            "authorization_servers": [str(provider.external_issuer)],
            "client_data": [
                {"server": str(provider.external_issuer), "client_id": provider.client_id, "name": provider.name},
            ],
            "scopes_supported": list(self._config.auth.oidc.scope),
        }
