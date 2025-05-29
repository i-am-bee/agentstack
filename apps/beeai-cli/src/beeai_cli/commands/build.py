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

import base64
import hashlib
import json
import re
import subprocess
import typing
import uuid
from contextlib import suppress
from datetime import timedelta

import anyio
import anyio.abc
import typer
from anyio import open_process, run_process
from httpx import AsyncClient, HTTPError
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_delay, wait_fixed

from beeai_cli.async_typer import AsyncTyper
from beeai_cli.console import console
from beeai_cli.utils import VMDriver, extract_messages


async def find_free_port():
    """Get a random free port assigned by the OS."""
    listener = await anyio.create_tcp_listener()
    port = listener.extra(anyio.abc.SocketAttribute.local_address)[1]
    await listener.aclose()
    return port


app = AsyncTyper()


@app.command("build")
async def build(
    context: typing.Annotated[str, typer.Argument(help="Docker context for the agent")] = ".",
    tag: typing.Annotated[str | None, typer.Option(help="Docker tag for the agent")] = None,
    multi_platform: bool | None = False,
    quiet: typing.Annotated[bool, typer.Option(hidden=True)] = False,
    import_image: typing.Annotated[
        bool, typer.Option("--import/--no-import", is_flag=True, help="Import the image into BeeAI platform")
    ] = True,
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "beeai-platform",
    vm_driver: typing.Annotated[VMDriver, typer.Option(hidden=True)] = None,
):
    try:
        await run_process("which docker", check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            "The 'docker' command is not found on the system. Please install docker or similar and try again"
        ) from e
    image_id = "beeai-agent-build-tmp:latest"
    port = await find_free_port()
    if multi_platform:
        build_command = "docker buildx build --platform=linux/amd64,linux/arm64 --load"
    else:
        build_command = "docker build"

    with console.status("building agent image", spinner="dots"):
        await run_process(
            f"{build_command} {context} -t {image_id}",
            check=True,
            stdout=subprocess.DEVNULL if quiet else None,
            stderr=subprocess.DEVNULL if quiet else None,
        )

    response = None

    container_id = uuid.uuid4()

    async with (
        await open_process(
            f"docker run --name {container_id} --rm -p {port}:8000 -e HOST=0.0.0.0 -e PORT=8000 {image_id}"
        ) as process,
    ):
        try:
            with console.status("extracting agent metadata", spinner="dots"):
                async for attempt in AsyncRetrying(
                    stop=stop_after_delay(timedelta(seconds=30)),
                    wait=wait_fixed(timedelta(seconds=0.5)),
                    retry=retry_if_exception_type(HTTPError),
                    reraise=True,
                ):
                    with attempt:
                        async with AsyncClient() as client:
                            resp = await client.get(f"http://localhost:{port}/agents", timeout=1)
                            resp.raise_for_status()
                            response = resp.json()
                            if "agents" not in response:
                                raise ValueError(f"Missing agents in response from server: {response}")
                process.terminate()
                with suppress(ProcessLookupError):
                    process.kill()
        except BaseException as ex:
            raise RuntimeError(f"Failed to build agent: {extract_messages(ex)}") from ex
        finally:
            with suppress(BaseException):
                await run_process(f"docker kill {container_id}")

    context_hash = hashlib.sha256(context.encode()).hexdigest()[:6]
    context_shorter = re.sub(r"https?://", "", context).replace(r".git", "")
    tag = (tag or f"beeai.local/{re.sub(r'[^a-zA-Z0-9._-]+', '-', context_shorter)[:32]}{context_hash}:latest").lower()
    await run_process(
        command=(
            f"{build_command} {context} -t {tag} "
            f"--label=beeai.dev.agent.yaml={base64.b64encode(json.dumps(response).encode()).decode()}"
        ),
        check=True,
    )
    console.print(f"✅ Successfully built agent: {tag}")
    if import_image:
        from beeai_cli.commands.platform import import_image

        import_image(tag, vm_name=vm_name, vm_driver=vm_driver)

    return tag, response["agents"]
