# Copyright 2025 © BeeAI a Series of LF Projects, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import contextlib
import enum
import re
import urllib
import urllib.parse
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any

import httpx
import psutil
from acp_sdk.client import Client
from httpx import BasicAuth, HTTPStatusError
from httpx._types import RequestFiles

from beeai_cli.configuration import Configuration

config = Configuration()
BASE_URL = str(config.host).rstrip("/")
API_BASE_URL = f"{BASE_URL}/api/v1/"
ACP_URL = f"{API_BASE_URL}acp"


class ProcessStatus(enum.StrEnum):
    not_running = "not_running"
    running_new = "running_new"
    running_old = "running_old"


def server_process_status(
    target_process="-m uvicorn beeai_server.application:app", recent_threshold=timedelta(minutes=10)
) -> ProcessStatus:
    try:
        for proc in psutil.process_iter(["cmdline", "create_time"]):
            cmdline = proc.info.get("cmdline", [])
            if not cmdline or target_process not in " ".join(cmdline):
                continue

            process_age = datetime.now() - datetime.fromtimestamp(proc.info["create_time"])
            return ProcessStatus.running_new if process_age < recent_threshold else ProcessStatus.running_old
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass

    return ProcessStatus.not_running


async def wait_for_api(initial_delay_seconds=5, wait: timedelta = timedelta(minutes=20)):
    await asyncio.sleep(initial_delay_seconds)
    start_time = datetime.now()
    while datetime.now() - start_time < wait:
        await asyncio.sleep(1)
        with contextlib.suppress(httpx.HTTPError, ConnectionError):
            await api_request("get", "providers")
            return True
    raise ConnectionError(f"Server did not start in {wait}. Please check your internet connection.")


async def api_request(
    method: str, path: str, json: dict | None = None, files: RequestFiles | None = None
) -> dict | None:
    """Make an API request to the server."""
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method,
            urllib.parse.urljoin(API_BASE_URL, path),
            json=json,
            files=files,
            timeout=60,
            auth=BasicAuth("beeai-admin", config.admin_password.get_secret_value()) if config.admin_password else None,
        )
        if response.is_error:
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
    method: str, path: str, json: dict | None = None, params: dict[str, Any] | None = None
) -> AsyncIterator[dict[str, Any]]:
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
        ) as response,
    ):
        response: httpx.Response
        if response.is_error:
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
async def acp_client() -> AsyncIterator[Client]:
    async with Client(base_url=ACP_URL) as client:
        yield client
