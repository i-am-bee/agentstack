# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import datetime
import functools
import importlib.resources
import os
import pathlib
import platform
import shutil
import sys
import textwrap
import typing

import httpx
import typer
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_delay, wait_fixed

from agentstack_cli.async_typer import AsyncTyper
from agentstack_cli.commands.platform.base_driver import BaseDriver, ImagePullMode
from agentstack_cli.commands.platform.lima_driver import LimaDriver
from agentstack_cli.commands.platform.wsl_driver import WSLDriver
from agentstack_cli.configuration import Configuration
from agentstack_cli.console import console
from agentstack_cli.utils import verbosity

app = AsyncTyper()

configuration = Configuration()


@functools.cache
def get_driver(vm_name: str = "agentstack") -> BaseDriver:
    has_lima = (importlib.resources.files("agentstack_cli") / "data" / "limactl").is_file() or shutil.which("limactl")
    has_vz = os.path.exists("/System/Library/Frameworks/Virtualization.framework")
    arch = "aarch64" if platform.machine().lower() == "arm64" else platform.machine().lower()
    has_qemu = bool(shutil.which(f"qemu-system-{arch}"))

    if platform.system() == "Windows" or shutil.which("wsl.exe"):
        return WSLDriver(vm_name=vm_name)
    elif has_lima and (has_vz or has_qemu):
        return LimaDriver(vm_name=vm_name)
    else:
        console.error("Could not find a compatible VM runtime.")
        if platform.system() == "Darwin":
            console.hint("This version of macOS is unsupported, please update the system.")
        elif platform.system() == "Linux":
            if not has_lima:
                console.hint(
                    "This Linux distribution is not suppored by Lima VM binary releases (required: glibc>=2.34). Manually install Lima VM >=1.2.1 through either:\n"
                    + "  - Your distribution's package manager, if available (https://repology.org/project/lima/versions)\n"
                    + "  - Homebrew, which uses its own separate glibc on Linux (https://brew.sh)\n"
                    + "  - Building it yourself, and ensuring that limactl is in PATH (https://lima-vm.io/docs/installation/source/)"
                )
            if not has_qemu:
                console.hint(
                    f"QEMU is needed on Linux, please install it and ensure that qemu-system-{arch} is in PATH. Refer to https://www.qemu.org/download/ for instructions."
                )
        sys.exit(1)


@app.command("start", help="Start Agent Stack platform. [Local only]")
async def start(
    set_values_list: typing.Annotated[
        list[str], typer.Option("--set", help="Set Helm chart values using <key>=<value> syntax", default_factory=list)
    ],
    image_pull_mode: typing.Annotated[
        ImagePullMode,
        typer.Option(
            "--image-pull-mode",
            help=textwrap.dedent(
                """\
                guest = pull all images inside VM
                host = pull unavailable images on host, then import all
                hybrid = import available images from host, pull the rest in VM
                skip = skip explicit pull step (Kubernetes will attempt to pull missing images)
                """
            ),
        ),
    ] = ImagePullMode.guest,
    values_file: typing.Annotated[
        pathlib.Path | None, typer.Option("-f", help="Set Helm chart values using yaml values file")
    ] = None,
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "agentstack",
    verbose: typing.Annotated[bool, typer.Option("-v", "--verbose", help="Show verbose output")] = False,
    skip_login: typing.Annotated[bool, typer.Option(hidden=True)] = False,
    no_wait_for_platform: typing.Annotated[bool, typer.Option(hidden=True)] = False,
):
    import agentstack_cli.commands.server

    values_file_path = None
    if values_file:
        values_file_path = pathlib.Path(values_file)
        if not values_file_path.is_file():
            raise FileNotFoundError(f"Values file {values_file} not found.")

    with verbosity(verbose):
        driver = get_driver(vm_name=vm_name)
        await driver.create_vm()
        await driver.install_tools()
        await driver.deploy(
            set_values_list=set_values_list,
            values_file=values_file_path,
            image_pull_mode=image_pull_mode,
        )

        if not no_wait_for_platform:
            with console.status("Waiting for Agent Stack platform to be ready...", spinner="dots"):
                timeout = datetime.timedelta(minutes=20)
                async with httpx.AsyncClient() as client:
                    try:
                        async for attempt in AsyncRetrying(
                            stop=stop_after_delay(timeout),
                            wait=wait_fixed(datetime.timedelta(seconds=1)),
                            retry=retry_if_exception_type((httpx.HTTPError, ConnectionError)),
                            reraise=True,
                        ):
                            with attempt:
                                resp = await client.get("http://localhost:8333/healthcheck")
                                resp.raise_for_status()
                    except Exception as ex:
                        raise ConnectionError(
                            f"Server did not start in {timeout}. Please check your internet connection."
                        ) from ex

        console.success("Agent Stack platform started successfully!")

        if any("phoenix.enabled=true" in value.lower() for value in set_values_list):
            console.print(
                textwrap.dedent("""\

                License Notice:
                When you enable Phoenix, be aware that Arize Phoenix is licensed under the Elastic License v2 (ELv2),
                which has specific terms regarding commercial use and distribution. By enabling Phoenix, you acknowledge
                that you are responsible for ensuring compliance with the ELv2 license terms for your specific use case.
                Please review the Phoenix license (https://github.com/Arize-ai/phoenix/blob/main/LICENSE) before enabling
                this feature in production environments.
                """),
                style="dim",
            )

        if not skip_login:
            await agentstack_cli.commands.server.server_login("http://localhost:8333")


@app.command("stop", help="Stop Agent Stack platform. [Local only]")
async def stop(
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "agentstack",
    verbose: typing.Annotated[bool, typer.Option("-v", "--verbose", help="Show verbose output")] = False,
):
    with verbosity(verbose):
        driver = get_driver(vm_name=vm_name)
        if not await driver.status():
            console.info("Agent Stack platform not found. Nothing to stop.")
            return
        await driver.stop()
        console.success("Agent Stack platform stopped successfully.")


@app.command("delete", help="Delete Agent Stack platform. [Local only]")
async def delete(
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "agentstack",
    verbose: typing.Annotated[bool, typer.Option("-v", "--verbose", help="Show verbose output")] = False,
):
    with verbosity(verbose):
        driver = get_driver(vm_name=vm_name)
        await driver.delete()
        console.success("Agent Stack platform deleted successfully.")


@app.command("import", help="Import a local docker image into the Agent Stack platform. [Local only]")
async def import_image_cmd(
    tag: typing.Annotated[str, typer.Argument(help="Docker image tag to import")],
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "agentstack",
    verbose: typing.Annotated[bool, typer.Option("-v", "--verbose", help="Show verbose output")] = False,
):
    with verbosity(verbose):
        driver = get_driver(vm_name=vm_name)
        if (await driver.status()) != "running":
            console.error("Agent Stack platform is not running.")
            sys.exit(1)
        await driver.import_images(tag)


@app.command("exec", help="For debugging -- execute a command inside the Agent Stack platform VM. [Local only]")
async def exec_cmd(
    command: typing.Annotated[list[str] | None, typer.Argument()] = None,
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "agentstack",
    verbose: typing.Annotated[bool, typer.Option("-v", "--verbose", help="Show verbose output")] = False,
):
    with verbosity(verbose, show_success_status=False):
        driver = get_driver(vm_name=vm_name)
        if (await driver.status()) != "running":
            console.error("Agent Stack platform is not running.")
            sys.exit(1)
        await driver.exec(command or ["/bin/bash"])
