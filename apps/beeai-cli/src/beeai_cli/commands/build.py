# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import base64
import hashlib
import json
import re
import sys
import typing
import uuid
from contextlib import suppress
from datetime import timedelta

import anyio
import anyio.abc
import typer
from a2a.utils import AGENT_CARD_WELL_KNOWN_PATH
from anyio import open_process
from httpx import AsyncClient, HTTPError
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_delay, wait_fixed

from beeai_cli.async_typer import AsyncTyper
from beeai_cli.console import console
from beeai_cli.utils import capture_output, extract_messages, run_command, status, verbosity


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
    dockerfile: typing.Annotated[str | None, typer.Option(help="Use custom dockerfile path")] = None,
    tag: typing.Annotated[str | None, typer.Option(help="Docker tag for the agent")] = None,
    multi_platform: bool | None = False,
    push: typing.Annotated[bool, typer.Option(help="Push the image to the target registry.")] = False,
    import_image: typing.Annotated[
        bool, typer.Option("--import/--no-import", is_flag=True, help="Import the image into BeeAI platform")
    ] = True,
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "beeai-platform",
    verbose: typing.Annotated[bool, typer.Option("-v")] = False,
):
    with verbosity(verbose):
        await run_command(["which", "docker"], "Checking docker")
        image_id = "beeai-agent-build-tmp:latest"
        port = await find_free_port()
        dockerfile_args = ("-f", dockerfile) if dockerfile else ()

        await run_command(
            ["docker", "build", context, *dockerfile_args, "-t", image_id],
            "Building agent image",
        )

        agent_card = None

        container_id = uuid.uuid4()

        with status("Extracting agent metadata"):
            async with (
                await open_process(
                    f"docker run --name {container_id} --rm -p {port}:8000 -e HOST=0.0.0.0 -e PORT=8000 {image_id}",
                ) as process,
            ):
                async with capture_output(process) as task_group:
                    try:
                        async for attempt in AsyncRetrying(
                            stop=stop_after_delay(timedelta(seconds=30)),
                            wait=wait_fixed(timedelta(seconds=0.5)),
                            retry=retry_if_exception_type(HTTPError),
                            reraise=True,
                        ):
                            with attempt:
                                async with AsyncClient() as client:
                                    resp = await client.get(
                                        f"http://localhost:{port}{AGENT_CARD_WELL_KNOWN_PATH}", timeout=1
                                    )
                                    resp.raise_for_status()
                                    agent_card = resp.json()
                        process.terminate()
                        with suppress(ProcessLookupError):
                            process.kill()
                    except BaseException as ex:
                        raise RuntimeError(f"Failed to build agent: {extract_messages(ex)}") from ex
                    finally:
                        task_group.cancel_scope.cancel()
                        with suppress(BaseException):
                            await run_command(["docker", "kill", container_id], "Killing container")
                        with suppress(ProcessLookupError):
                            process.kill()

        context_hash = hashlib.sha256((context + (dockerfile or "")).encode()).hexdigest()[:6]
        context_shorter = re.sub(r"https?://", "", context).replace(r".git", "")
        context_shorter = re.sub(r"[^a-zA-Z0-9_-]+", "-", context_shorter)[:32].lstrip("-") or "provider"
        tag = (tag or f"beeai.local/{context_shorter}-{context_hash}:latest").lower()
        await run_command(
            command=[
                *(
                    ["docker", "buildx", "build", "--platform=linux/amd64,linux/arm64"]
                    if multi_platform
                    else ["docker", "build"]
                ),
                "--push" if push else "--load",
                context,
                *dockerfile_args,
                "-t",
                tag,
                f"--label=beeai.dev.agent.json={base64.b64encode(json.dumps(agent_card).encode()).decode()}",
            ],
            message="Adding agent labels to container",
            check=True,
        )
        console.print(f"✅ Successfully built agent: {tag}")
        if import_image:
            from beeai_cli.commands.platform import get_driver

            driver = get_driver(vm_name=vm_name)
            if (await driver.status()) != "running":
                console.print("[red]BeeAI platform is not running.[/red]")
                sys.exit(1)
            await driver.import_image(tag)

        return tag, agent_card
