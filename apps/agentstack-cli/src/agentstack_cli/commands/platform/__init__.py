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
from agentstack_sdk.platform import Provider
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_delay, wait_fixed

from agentstack_cli.async_typer import AsyncTyper
from agentstack_cli.commands.platform.base_driver import BaseDriver
from agentstack_cli.commands.platform.lima_driver import LimaDriver
from agentstack_cli.commands.platform.wsl_driver import WSLDriver
from agentstack_cli.console import console
from agentstack_cli.utils import verbosity

app = AsyncTyper()


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


@app.command("start")
async def start(
    set_values_list: typing.Annotated[
        list[str], typer.Option("--set", help="Set Helm chart values using <key>=<value> syntax", default_factory=list)
    ],
    import_images: typing.Annotated[
        list[str],
        typer.Option(
            "--import", help="Import an image from a local Docker CLI into Agent Stack platform", default_factory=list
        ),
    ],
    values_file: typing.Annotated[
        pathlib.Path | None, typer.Option("-f", help="Set Helm chart values using yaml values file")
    ] = None,
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "agentstack",
    verbose: typing.Annotated[bool, typer.Option("-v", help="Show verbose output")] = False,
):
    """Start Agent Stack platform."""
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
        await driver.deploy(set_values_list=set_values_list, values_file=values_file_path, import_images=import_images)

        with console.status("Waiting for Agent Stack platform to be ready...", spinner="dots"):
            timeout = datetime.timedelta(minutes=20)
            try:
                async for attempt in AsyncRetrying(
                    stop=stop_after_delay(timeout),
                    wait=wait_fixed(datetime.timedelta(seconds=1)),
                    retry=retry_if_exception_type((httpx.HTTPError, ConnectionError)),
                    reraise=True,
                ):
                    with attempt:
                        await Provider.list()
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

        await agentstack_cli.commands.server.server_login("http://localhost:8333")


@app.command("stop")
async def stop(
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "agentstack",
    verbose: typing.Annotated[bool, typer.Option("-v", help="Show verbose output")] = False,
):
    """Stop Agent Stack platform."""
    with verbosity(verbose):
        driver = get_driver(vm_name=vm_name)
        if not await driver.status():
            console.info("Agent Stack platform not found. Nothing to stop.")
            return
        await driver.stop()
        console.success("Agent Stack platform stopped successfully.")


@app.command("delete")
async def delete(
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "agentstack",
    verbose: typing.Annotated[bool, typer.Option("-v", help="Show verbose output")] = False,
):
    """Delete Agent Stack platform."""
    with verbosity(verbose):
        driver = get_driver(vm_name=vm_name)
        await driver.delete()
        console.success("Agent Stack platform deleted successfully.")


@app.command("import")
async def import_image_cmd(
    tag: typing.Annotated[str, typer.Argument(help="Docker image tag to import")],
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "agentstack",
    verbose: typing.Annotated[bool, typer.Option("-v", help="Show verbose output")] = False,
):
    """Import a local docker image into the Agent Stack platform."""
    with verbosity(verbose):
        driver = get_driver(vm_name=vm_name)
        if (await driver.status()) != "running":
            console.error("Agent Stack platform is not running.")
            sys.exit(1)
        await driver.import_image(tag)


@app.command("exec")
async def exec_cmd(
    command: typing.Annotated[list[str] | None, typer.Argument()] = None,
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "agentstack",
    verbose: typing.Annotated[bool, typer.Option("-v", help="Show verbose output")] = False,
):
    """For debugging -- execute a command inside the Agent Stack platform VM."""
    with verbosity(verbose, show_success_status=False):
        driver = get_driver(vm_name=vm_name)
        if (await driver.status()) != "running":
            console.error("Agent Stack platform is not running.")
            sys.exit(1)
        await driver.exec(command or ["/bin/bash"])
