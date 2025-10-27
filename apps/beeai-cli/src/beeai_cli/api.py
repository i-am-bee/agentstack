# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
import re
import urllib
import urllib.parse
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Any

import httpx
import openai
from a2a.client import Client, ClientConfig, ClientFactory
from a2a.types import AgentCard
from httpx import HTTPStatusError
from httpx._types import RequestFiles

from beeai_cli import configuration
from beeai_cli.configuration import Configuration

config = Configuration()

API_BASE_URL = "api/v1/"


async def api_request(
    method: str,
    path: str,
    json: dict | None = None,
    files: RequestFiles | None = None,
    params: dict[str, Any] | None = None,
    use_auth: bool = True,
) -> dict | None:
    """Make an API request to the server."""
    async with configuration.use_platform_client() as client:
        response = await client.request(
            method,
            urllib.parse.urljoin(API_BASE_URL, path),
            json=json,
            files=files,
            params=params,
            timeout=60,
            headers=(
                {"Authorization": f"Bearer {token}"}
                if use_auth and (token := config.auth_manager.load_auth_token())
                else {}
            ),
        )
        if response.is_error:
            error = ""
            try:
                error = response.json()
                error = error.get("detail", str(error))
            except Exception:
                response.raise_for_status()
            if response.status_code == 401:
                message = f'{error}\nexport BEEAI__ADMIN_PASSWORD="<PASSWORD>" to set the admin password.'
                raise HTTPStatusError(message=message, request=response.request, response=response)
            raise HTTPStatusError(message=error, request=response.request, response=response)
        if response.content:
            return response.json()


async def api_stream(
    method: str,
    path: str,
    json: dict | None = None,
    params: dict[str, Any] | None = None,
    use_auth: bool = True,
) -> AsyncIterator[dict[str, Any]]:
    """Make a streaming API request to the server."""
    import json as jsonlib

    async with (
        configuration.use_platform_client() as client,
        client.stream(
            method,
            urllib.parse.urljoin(API_BASE_URL, path),
            json=json,
            params=params,
            timeout=timedelta(hours=1).total_seconds(),
            headers=(
                {"Authorization": f"Bearer {token}"}
                if use_auth and (token := config.auth_manager.load_auth_token())
                else {}
            ),
        ) as response,
    ):
        response: httpx.Response
        if response.is_error:
            error = ""
            try:
                [error] = [jsonlib.loads(message) async for message in response.aiter_text()]
                error = error.get("detail", str(error))
            except Exception:
                response.raise_for_status()
            raise HTTPStatusError(message=error, request=response.request, response=response)
        async for line in response.aiter_lines():
            if line:
                yield jsonlib.loads(re.sub("^data:", "", line).strip())


@asynccontextmanager
async def a2a_client(agent_card: AgentCard, use_auth: bool = True) -> AsyncIterator[Client]:
    async with httpx.AsyncClient(
        headers=(
            {"Authorization": f"Bearer {token}"}
            if use_auth and (token := config.auth_manager.load_auth_token())
            else {}
        ),
        follow_redirects=True,
        timeout=timedelta(hours=1).total_seconds(),
    ) as httpx_client:
        yield ClientFactory(ClientConfig(httpx_client=httpx_client)).create(card=agent_card)


@asynccontextmanager
async def openai_client() -> AsyncIterator[openai.AsyncOpenAI]:
    async with Configuration().use_platform_client() as platform_client:
        verify = os.environ.get("CLIENT_VERIFY_TLS", True)
        if verify == "False":
            verify = False
        # need to remove the bearer token from the default headers
        default_headers = platform_client.headers.copy()
        default_headers.pop("Authorization", None)
        yield openai.AsyncOpenAI(
            api_key=platform_client.headers.get("Authorization", "").removeprefix("Bearer ") or "dummy",
            base_url=urllib.parse.urljoin(str(platform_client.base_url), urllib.parse.urljoin(API_BASE_URL, "openai")),
            default_headers=default_headers,
            http_client=httpx.AsyncClient(verify=verify),
        )
