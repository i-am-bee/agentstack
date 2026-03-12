# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
from typing import Any

import httpx

from agentstack_server.configuration import KagentiConfiguration

logger = logging.getLogger(__name__)


class KagentiClient:
    def __init__(self, configuration: KagentiConfiguration):
        self._config = configuration
        self._token: str | None = None

    async def _get_token(self) -> str | None:
        """Get OAuth2 token via client credentials grant."""
        if not self._config.auth_token_url or not self._config.client_id or not self._config.client_secret:
            return None

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._config.auth_token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self._config.client_id,
                    "client_secret": self._config.client_secret.get_secret_value(),
                },
            )
            response.raise_for_status()
            return response.json()["access_token"]

    async def list_agents(self) -> list[dict[str, Any]]:
        """Fetch all agents from kagenti backend API across configured namespaces.

        Returns a list of agent dicts, each with at least 'name', 'namespace', and 'url' keys.
        """
        headers: dict[str, str] = {}
        token = await self._get_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"

        result = []
        async with httpx.AsyncClient(timeout=30) as client:
            for namespace in self._config.namespaces:
                try:
                    response = await client.get(
                        f"{self._config.api_url}/api/v1/agents",
                        params={"namespace": namespace},
                        headers=headers,
                    )
                    response.raise_for_status()
                    data = response.json()
                except httpx.HTTPError as e:
                    logger.warning("Failed to list agents in namespace %s: %s", namespace, e)
                    continue

                agents = data.get("items", [])

                for agent in agents:
                    name = agent.get("name", "")
                    agent_namespace = agent.get("namespace", namespace)

                    # Construct service URL from k8s naming convention
                    url = f"http://{name}.{agent_namespace}.svc.cluster.local:8080"

                    result.append(
                        {
                            "name": name,
                            "namespace": agent_namespace,
                            "url": url,
                            "status": agent.get("status", "unknown"),
                        }
                    )

        return result
