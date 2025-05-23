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

import contextlib
import enum
import json
import re
import subprocess
import time
import urllib
import urllib.parse
from contextlib import asynccontextmanager
from datetime import timedelta, datetime
from typing import AsyncIterator, Any

import httpx
import psutil
from acp_sdk.client import Client
from httpx import HTTPStatusError
from httpx._types import RequestFiles

from beeai_cli.configuration import Configuration
from beeai_cli.console import console, err_console
from beeai_cli.utils import format_error

config = Configuration()
BASE_URL = str(config.host).rstrip("/")
API_BASE_URL = f"{BASE_URL}/api/v1/"
ACP_URL = f"{API_BASE_URL}acp"


class BrewServiceStatus(enum.StrEnum):
    not_installed = "not_installed"
    stopped = "stopped"
    started = "started"


def brew_service_status() -> BrewServiceStatus:
    beeai_service = None
    with contextlib.suppress(Exception):
        services = json.loads(subprocess.check_output(["brew", "services", "list", "--json"]))
        beeai_service = next((service for service in services if service["name"] == "beeai"), None)
    if not beeai_service:
        return BrewServiceStatus.not_installed
    elif beeai_service["status"] == "started":
        return BrewServiceStatus.started
    else:
        return BrewServiceStatus.stopped


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


async def resolve_connection_error():
    if BASE_URL != "http://localhost:8333":
        err_console.print(format_error("ConnectError", "Could not connect to the BeeAI service."))
        err_console.print(
            f'💡 [yellow]HINT[/yellow]: You have set the BeeAI host to "[bold]{BASE_URL}[/bold]" -- is this correct?'
        )
        exit(1)

    with console.status(
        "Starting the BeeAI service, this might take a few minutes, please stand by...", spinner="dots"
    ):
        try:
            import beeai_cli.commands.platform

            beeai_cli.commands.platform.start()
            await wait_for_api()
            await wait_for_agents()
        except Exception:
            err_console.print(format_error("ConnectError", "We failed to automatically start the BeeAI service."))
            err_console.print(
                "💡 [yellow]HINT[/yellow]: Try starting the service manually with: [green]beeai platform start[/green]"
            )
            exit(1)


async def wait_for_agents(initial_delay_seconds=5, wait_seconds=180):
    time.sleep(initial_delay_seconds)
    for i in range(wait_seconds):
        time.sleep(1)
        if all(
            item["status"] in ["ready", "installing", "not_installed", "running"]
            for item in (await api_request("get", "providers"))["items"]
        ):
            return True
    else:
        return False


async def wait_for_api(initial_delay_seconds=5, wait_seconds=300):
    time.sleep(initial_delay_seconds)
    for i in range(wait_seconds):
        time.sleep(1)
        with contextlib.suppress(httpx.ConnectError, ConnectionError):
            await api_request("get", "providers")
            return True
    else:
        return False


async def api_request(
    method: str, path: str, json: dict | None = None, files: RequestFiles | None = None
) -> dict | None:
    """Make an API request to the server."""
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method, urllib.parse.urljoin(API_BASE_URL, path), json=json, files=files, timeout=60
        )
        if response.is_error:
            try:
                error = response.json()
                error = error.get("detail", str(error))
            except Exception:
                response.raise_for_status()
            raise HTTPStatusError(message=error, request=response.request, response=response)
        if response.content:
            return response.json()


async def api_stream(
    method: str, path: str, json: dict | None = None, params: dict[str, Any] | None = None
) -> AsyncIterator[dict[str, Any]]:
    """Make a streaming API request to the server."""
    import json as jsonlib

    async with httpx.AsyncClient() as client:
        async with client.stream(
            method,
            urllib.parse.urljoin(API_BASE_URL, path),
            json=json,
            params=params,
            timeout=timedelta(hours=1).total_seconds(),
        ) as response:
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
