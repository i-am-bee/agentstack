# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import enum
import re
import urllib
import urllib.parse
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timedelta
from typing import Any

import httpx
import openai
import psutil
from a2a.client import Client, ClientConfig, ClientFactory
from a2a.types import AgentCard
from httpx import HTTPStatusError
from httpx._types import RequestFiles

from beeai_cli.configuration import Configuration

config = Configuration()
BASE_URL = server if (server := config.auth_manager.get_active_server()) else "http://localhost:8333"
API_BASE_URL = f"{BASE_URL}/api/v1/"


class ProcessStatus(enum.StrEnum):
    NOT_RUNNING = "not_running"
    RUNNING_NEW = "running_new"
    RUNNING_OLD = "running_old"


def server_process_status(
    target_process="-m uvicorn beeai_server.application:app", recent_threshold=timedelta(minutes=10)
) -> ProcessStatus:
    try:
        for proc in psutil.process_iter(["cmdline", "create_time"]):
            cmdline = proc.info.get("cmdline", [])
            if not cmdline or target_process not in " ".join(cmdline):
                continue

            process_age = datetime.now() - datetime.fromtimestamp(proc.info["create_time"])
            return ProcessStatus.RUNNING_NEW if process_age < recent_threshold else ProcessStatus.RUNNING_OLD
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass

    return ProcessStatus.NOT_RUNNING


async def set_auth_header():
    if not (token := config.auth_manager.load_auth_token()):
        raise RuntimeError("No token found. Please run `beeai login` first.")
    return f"Bearer {token}"


async def api_request(
    method: str,
    path: str,
    json: dict | None = None,
    files: RequestFiles | None = None,
    params: dict[str, Any] | None = None,
    use_auth: bool = True,
) -> dict | None:
    headers = {}
    if use_auth:
        with suppress(RuntimeError):
            headers["Authorization"] = await set_auth_header()
    """Make an API request to the server."""
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method,
            urllib.parse.urljoin(API_BASE_URL, path),
            json=json,
            files=files,
            params=params,
            timeout=60,
            headers=headers,
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
    headers = {}
    with suppress(RuntimeError):
        if use_auth:
            headers["Authorization"] = await set_auth_header()

    """Make a streaming API request to the server."""
    import json as jsonlib

    async with (
        httpx.AsyncClient() as client,
        client.stream(
            method,
            urllib.parse.urljoin(API_BASE_URL, path),
            json=json,
            params=params,
            timeout=timedelta(hours=1).total_seconds(),
            headers=headers,
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
    headers = {}
    if use_auth:
        with suppress(RuntimeError):
            headers["Authorization"] = await set_auth_header()

    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as httpx_client:
        yield ClientFactory(ClientConfig(httpx_client=httpx_client)).create(card=agent_card)


@asynccontextmanager
async def openai_client() -> AsyncIterator[openai.AsyncOpenAI]:
    async with Configuration().use_platform_client() as platform_client:
        yield openai.AsyncOpenAI(
            api_key=platform_client.headers.get("Authorization", "").removeprefix("Bearer ") or "dummy",
            base_url=urllib.parse.urljoin(API_BASE_URL, "openai"),
            default_headers=platform_client.headers,
        )
