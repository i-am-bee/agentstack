# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging

from kink import inject

from beeai_server.configuration import Configuration

logger = logging.getLogger(__name__)


@inject
class AuthService:
    def __init__(self, configuration: Configuration):
        self._config = configuration

    def protected_resource_metadata(self) -> dict:
        resource_id = f"http://localhost:{self._config.port}"  # TODO
        providers = self._config.auth.oidc.providers
        authorization_server = [str(p.issuer) for p in providers if p.issuer is not None]

        return {
            "resource_id": resource_id,
            "authorization_servers": authorization_server,
            "scopes_supported": list(self._config.auth.oidc.scope),
        }
