# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

import httpx


class KagentiClient:
    """Lightweight client for kagenti backend API."""

    def __init__(self, base_url: str, access_token: str):
        self._base_url = base_url.rstrip("/")
        self._headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    async def create_agent(self, request: dict[str, Any]) -> dict[str, Any]:
        """Create an agent in kagenti.

        POST /api/v1/agents/
        """
        async with httpx.AsyncClient(follow_redirects=True) as client:
            resp = await client.post(
                f"{self._base_url}/api/v1/agents/",
                json=request,
                headers=self._headers,
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_agent(self, namespace: str, name: str) -> dict[str, Any]:
        """Get agent details.

        GET /api/v1/agents/{namespace}/{name}
        """
        async with httpx.AsyncClient(follow_redirects=True) as client:
            resp = await client.get(
                f"{self._base_url}/api/v1/agents/{namespace}/{name}",
                headers=self._headers,
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()

    async def delete_agent(self, namespace: str, name: str) -> None:
        """Delete an agent from kagenti.

        DELETE /api/v1/agents/{namespace}/{name}
        """
        async with httpx.AsyncClient(follow_redirects=True) as client:
            resp = await client.delete(
                f"{self._base_url}/api/v1/agents/{namespace}/{name}",
                headers=self._headers,
                timeout=30,
            )
            resp.raise_for_status()

    async def list_agents(self, namespace: str | None = None) -> list[dict[str, Any]]:
        """List agents, optionally filtered by namespace.

        GET /api/v1/agents/
        """
        params = {"namespace": namespace} if namespace else {}
        async with httpx.AsyncClient(follow_redirects=True) as client:
            resp = await client.get(
                f"{self._base_url}/api/v1/agents/",
                headers=self._headers,
                params=params,
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()
