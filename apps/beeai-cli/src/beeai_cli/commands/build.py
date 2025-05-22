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
import json
import subprocess
import sys
import typing
import uuid
from contextlib import suppress
from datetime import timedelta
from typing import Optional

import anyio
import anyio.abc
import typer
from anyio import open_process

from anyio import run_process
from httpx import HTTPError, AsyncClient
from tenacity import AsyncRetrying, wait_fixed, stop_after_delay, retry_if_exception_type

from beeai_cli import Configuration
from beeai_cli.async_typer import AsyncTyper
from beeai_cli.console import console
from beeai_cli.utils import extract_messages, import_images_to_vm


async def find_free_port():
    """Get a random free port assigned by the OS."""
    listener = await anyio.create_tcp_listener()
    port = listener.extra(anyio.abc.SocketAttribute.local_address)[1]
    await listener.aclose()
    return port


app = AsyncTyper()


async def save_image(image_id: str):
    with console.status("Saving image", spinner="dots"):
        path = str(Configuration().home / "images" / image_id.replace("/", "_")) + ".tar"
        await run_process(["docker", "image", "save", "-o", path, image_id])


@app.command("build")
async def build(
    context: Optional[str] = typer.Argument(".", help="Docker context for the agent"),
    tag: Optional[str] = typer.Option(None, help="Docker tag for the agent"),
    multi_platform: Optional[bool] = False,
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "beeai",
    import_images: typing.Annotated[
        bool, typer.Option(help="Load images from the ~/.beeai/images folder on host into the VM")
    ] = True,
):
    try:
        await run_process("which docker", check=True)
    except subprocess.CalledProcessError:
        raise RuntimeError(
            "The 'docker' command is not found on the system. Please install docker or similar and try again"
        )
    image_id = "beeai-agent-build-tmp:latest"
    port = await find_free_port()
    if multi_platform:
        build_command = "docker buildx build --platform=linux/amd64,linux/amd64/v2,linux/amd64/v3,linux/386"
    else:
        build_command = "docker build"

    await run_process(f"{build_command} {context} -t {image_id}", check=True, stdout=sys.stdout, stderr=sys.stderr)

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
                with anyio.move_on_after(delay=1):
                    process.terminate()
                with suppress(ProcessLookupError):
                    process.kill()
        except BaseException as ex:
            raise RuntimeError(f"Failed to build agent: {extract_messages(ex)}") from ex
        finally:
            with suppress(BaseException):
                await run_process(f"docker kill {container_id}")

    if len(response["agents"]) > 1 and not tag:
        raise ValueError(
            "The server contains more than one agent - the image naming is ambiguous."
            "please provide a specific docker tag to export, e.g. `beeai build --tag my-agent:latest"
        )

    tag = tag or f"beeai.local/{response['agents'][0]['name']}:latest"
    await run_process(
        command=(
            f"{build_command} {context} -t {tag} "
            f"--label=beeai.dev.agent.yaml={base64.b64encode(json.dumps(response).encode()).decode()}"
        ),
        check=True,
    )
    console.print(f"✅ Successfully built agent: {tag}")
    await save_image(image_id=tag)
    if import_images:
        import_images_to_vm(vm_name)
