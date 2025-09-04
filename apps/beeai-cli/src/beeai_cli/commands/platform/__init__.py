# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import contextlib
import datetime
import functools
import importlib.resources
import os
import platform
import shutil
import sys
import textwrap
import typing

import httpx
import typer
from beeai_sdk.platform import Provider

from beeai_cli.async_typer import AsyncTyper
from beeai_cli.commands.platform.base_driver import BaseDriver
from beeai_cli.commands.platform.lima_driver import LimaDriver
from beeai_cli.commands.platform.wsl_driver import WSLDriver
from beeai_cli.console import console
from beeai_cli.utils import verbosity

app = AsyncTyper()


@functools.cache
def get_driver(vm_name: str = "beeai-platform") -> BaseDriver:
    has_lima = (importlib.resources.files("beeai_cli") / "data" / "limactl").is_file() or shutil.which("limactl")
    has_vz = os.path.exists("/System/Library/Frameworks/Virtualization.framework")
    arch = "aarch64" if platform.machine().lower() == "arm64" else platform.machine().lower()
    has_qemu = bool(shutil.which(f"qemu-system-{arch}"))

    if platform.system() == "Windows" or shutil.which("wsl.exe"):
        return WSLDriver(vm_name=vm_name)
    elif has_lima and (has_vz or has_qemu):
        return LimaDriver(vm_name=vm_name)
    else:
        console.print(
            "[red]Error: Could not find a compatible VM runtime. Please follow the installation instructions at https://docs.beeai.dev/introduction/installation[/red]"
        )
        if platform.system() == "Darwin":
            console.print("💡 [yellow]HINT[/yellow]: This version of macOS is unsupported, please update the system.")
        elif platform.system() == "Linux":
            if not has_lima:
                console.print(
                    "💡 [yellow]HINT[/yellow]: This Linux distribution is not suppored by Lima VM binary releases. Manually install Lima VM through your distribution's package manager, or build it yourself, and ensure that limactl is in PATH."
                )
            if not has_qemu:
                console.print(
                    f"💡 [yellow]HINT[/yellow]: QEMU is needed on Linux, please install it and ensure that qemu-system-{arch} is in PATH."
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
            "--import", help="Import an image from a local Docker CLI into BeeAI platform", default_factory=list
        ),
    ],
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "beeai-platform",
    verbose: typing.Annotated[bool, typer.Option("-v", help="Show verbose output")] = False,
):
    """Start BeeAI platform."""
    with verbosity(verbose):
        driver = get_driver(vm_name=vm_name)
        await driver.create_vm()
        await driver.install_tools()
        await driver.deploy(set_values_list=set_values_list, import_images=import_images)

        with console.status("Waiting for BeeAI platform to be ready...", spinner="dots"):
            start_time = datetime.datetime.now()
            timeout = datetime.timedelta(minutes=20)
            await asyncio.sleep(5)

            while datetime.datetime.now() - start_time < timeout:
                await asyncio.sleep(1)
                with contextlib.suppress(httpx.HTTPError, ConnectionError):
                    await Provider.list()
                    break
            else:
                raise ConnectionError(f"Server did not start in {timeout}. Please check your internet connection.")

        console.print("[green]BeeAI platform started successfully![/green]")

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


@app.command("stop")
async def stop(
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "beeai-platform",
    verbose: typing.Annotated[bool, typer.Option("-v", help="Show verbose output")] = False,
):
    """Stop BeeAI platform."""
    with verbosity(verbose):
        driver = get_driver(vm_name=vm_name)
        if not await driver.status():
            console.print("BeeAI platform not found. Nothing to stop.")
            return
        await driver.stop()
        console.print("[green]BeeAI platform stopped successfully.[/green]")


@app.command("delete")
async def delete(
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "beeai-platform",
    verbose: typing.Annotated[bool, typer.Option("-v", help="Show verbose output")] = False,
):
    """Delete BeeAI platform."""
    with verbosity(verbose):
        driver = get_driver(vm_name=vm_name)
        await driver.delete()
        console.print("[green]BeeAI platform deleted successfully.[/green]")


@app.command("import")
async def import_image_cmd(
    tag: typing.Annotated[str, typer.Argument(help="Docker image tag to import")],
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "beeai-platform",
    verbose: typing.Annotated[bool, typer.Option("-v", help="Show verbose output")] = False,
):
    """Import a local docker image into the BeeAI platform."""
    with verbosity(verbose):
        driver = get_driver(vm_name=vm_name)
        if (await driver.status()) != "running":
            console.print("[red]BeeAI platform is not running.[/red]")
            sys.exit(1)
        await driver.import_image(tag)


@app.command("exec")
async def exec_cmd(
    command: typing.Annotated[list[str] | None, typer.Argument()] = None,
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "beeai-platform",
    verbose: typing.Annotated[bool, typer.Option("-v", help="Show verbose output")] = False,
):
    """For debugging -- execute a command inside the BeeAI platform VM."""
    with verbosity(verbose, show_success_status=False):
        driver = get_driver(vm_name=vm_name)
        if (await driver.status()) != "running":
            console.print("[red]BeeAI platform is not running.[/red]")
            sys.exit(1)
        await driver.exec(command or ["/bin/bash"])
