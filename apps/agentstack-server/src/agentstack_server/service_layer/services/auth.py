# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging

from kink import inject

from agentstack_server.configuration import Configuration

logger = logging.getLogger(__name__)


@inject
class AuthService:
    def __init__(self, configuration: Configuration):
        self._config = configuration

    def protected_resource_metadata(self, *, resource: str) -> dict:
        return {
            "resource": resource,
            "authorization_servers": [str(p.issuer) for p in self._config.auth.oidc.providers if p.issuer is not None],
            "scopes_supported": list(self._config.auth.oidc.scope),
        }
