# SPDX-License-Identifier: Apache-2.0
import functools
import importlib.metadata
import os
import platform
import shutil
import subprocess
import sys
import typing

import httpx
import packaging.version
import pydantic
import typer
from InquirerPy import inquirer

import beeai_cli.commands.platform
from beeai_cli.async_typer import AsyncTyper
from beeai_cli.commands.model import setup as model_setup
from beeai_cli.configuration import Configuration
from beeai_cli.console import console
from beeai_cli.utils import run_command, verbosity

app = AsyncTyper()
configuration = Configuration()


@functools.cache
def _path() -> str:
    # These are PATHs where `uv` installs itself when installed through own install script
    # Package managers may install elsewhere, but that location should already be in PATH
    return os.pathsep.join(
        [
            *([xdg_bin_home] if (xdg_bin_home := os.getenv("XDG_BIN_HOME")) else []),
            *([os.path.realpath(f"{xdg_data_home}/../bin")] if (xdg_data_home := os.getenv("XDG_DATA_HOME")) else []),
            os.path.expanduser("~/.local/bin"),
            os.getenv("PATH", ""),
        ]
    )


@app.command("version")
async def version(verbose: typing.Annotated[bool, typer.Option("-v", help="Show verbose output")] = False):
    """Print version of the BeeAI CLI."""
    with verbosity(verbose=verbose):
        cli_version = importlib.metadata.version("beeai-cli")
        platform_version = await beeai_cli.commands.platform.get_driver().version()

        latest_cli_version: str | None = None
        with console.status("Checking for newer version...", spinner="dots"):
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("https://pypi.org/pypi/beeai-cli/json")
                PyPIPackageInfo = typing.TypedDict("PyPIPackageInfo", {"version": str})
                PyPIPackage = typing.TypedDict("PyPIPackage", {"info": PyPIPackageInfo})
                if response.status_code == 200:
                    latest_cli_version = pydantic.TypeAdapter(PyPIPackage).validate_json(response.text)["info"][
                        "version"
                    ]

        console.print()
        console.print(f"     beeai-cli version: [bold]{cli_version}[/bold]")
        console.print(
            f"beeai-platform version: [bold]{platform_version.replace('-', '') if platform_version is not None else 'not running'}[/bold]"
        )
        console.print()

        if latest_cli_version and packaging.version.parse(latest_cli_version) > packaging.version.parse(cli_version):
            console.hint(
                f"A newer version ([bold]{latest_cli_version}[/bold]) is available. Update using: [green]beeai self upgrade[/green]."
            )
        elif platform_version is None:
            console.hint("Start the BeeAI platform using: [green]beeai platform start[/green]")
        elif platform_version.replace("-", "") != cli_version:
            console.hint("Update the BeeAI platform using: [green]beeai platform start[/green]")
        else:
            console.success("Everything is up to date!")


@app.command("install")
async def install(
    verbose: typing.Annotated[bool, typer.Option("-v", help="Show verbose output")] = False,
):
    """Install BeeAI platform pre-requisites."""
    with verbosity(verbose=verbose):
        ready_to_start = False
        if platform.system() == "Linux":
            if shutil.which(
                f"qemu-system-{'aarch64' if platform.machine().lower() == 'arm64' else platform.machine().lower()}"
            ):
                ready_to_start = True
            else:
                if os.geteuid() != 0:
                    console.hint(
                        "You may be prompted for your password to install QEMU, as this needs root privileges."
                    )
                    os.execlp("sudo", sys.executable, *sys.argv)
                for cmd in [
                    ["apt", "install", "-y", "-qq", "qemu-system"],
                    ["dnf", "install", "-y", "-q", "@virtualization"],
                    ["pacman", "-S", "--noconfirm", "--noprogressbar", "qemu"],
                    ["zypper", "install", "-y", "-qq", "qemu"],
                    ["yum", "install", "-y", "-q", "qemu-kvm"],
                    ["emerge", "--quiet", "app-emulation/qemu"],
                ]:
                    if shutil.which(cmd[0]):
                        try:
                            await run_command(cmd, f"Installing QEMU with {cmd[0]}")
                            ready_to_start = True
                            break
                        except (subprocess.CalledProcessError, FileNotFoundError):
                            console.warning(
                                "Failed to install QEMU automatically. Please install QEMU manually before using BeeAI. Refer to https://www.qemu.org/download/ for instructions."
                            )
                            break
        elif platform.system() == "Darwin":
            ready_to_start = True

        already_started = False
        console.print()
        if (
            ready_to_start
            and await inquirer.confirm(  # pyright: ignore[reportPrivateImportUsage]
                message="Do you want to start the BeeAI platform now? Will run: beeai platform start", default=True
            ).execute_async()
        ):
            try:
                await beeai_cli.commands.platform.start(set_values_list=[], import_images=[], verbose=verbose)
                already_started = True
                console.print()
            except Exception:
                console.warning("Platform start failed. You can retry with [green]beeai platform start[/green].")

        already_configured = False
        if (
            already_started
            and await inquirer.confirm(  # pyright: ignore[reportPrivateImportUsage]
                message="Do you want to configure your LLM provider now? Will run: beeai model setup", default=True
            ).execute_async()
        ):
            try:
                await model_setup(verbose=verbose)
                already_configured = True
            except Exception:
                console.warning("Model setup failed. You can retry with [green]beeai model setup[/green].")

        if (
            already_configured
            and await inquirer.confirm(  # pyright: ignore[reportPrivateImportUsage]
                message="Do you want to open the web UI now? Will run: beeai ui", default=True
            ).execute_async()
        ):
            import webbrowser

            webbrowser.open("http://localhost:8334")

        console.print()
        console.success("Installation complete!")
        if not shutil.which("beeai", path=_path()):
            console.hint("Open a new terminal window to use the [green]beeai[/green] command.")
        if not already_started:
            console.hint("Start the BeeAI platform using: [green]beeai platform start[/green]")
        if not already_configured:
            console.hint("Configure your LLM provider using: [green]beeai model setup[/green]")
        console.hint(
            "Use [green]beeai ui[/green] to open the web GUI, or [green]beeai run chat[/green] to talk to an agent on the command line."
        )
        console.hint(
            "Run [green]beeai --help[/green] to learn about available commands, or check the documentation at https://docs.beeai.dev/"
        )


@app.command("upgrade")
async def upgrade(verbose: typing.Annotated[bool, typer.Option("-v", help="Show verbose output")] = False):
    """Upgrade BeeAI CLI and Platform to the latest version."""
    if not shutil.which("uv", path=_path()):
        console.error("Can't self-upgrade because 'uv' was not found.")
        raise typer.Exit(1)

    with verbosity(verbose=verbose):
        await run_command(
            ["uv", "tool", "install", "--force", "beeai-cli"],
            "Upgrading beeai-cli",
            env={"PATH": _path()},
        )
        await beeai_cli.commands.platform.start(set_values_list=[], import_images=[], verbose=verbose)
        await version(verbose=verbose)


@app.command("uninstall")
async def uninstall(
    verbose: typing.Annotated[bool, typer.Option("-v", help="Show verbose output")] = False,
):
    """Uninstall BeeAI CLI and Platform."""
    if not shutil.which("uv", path=_path()):
        console.error("Can't self-uninstall because 'uv' was not found.")
        raise typer.Exit(1)

    with verbosity(verbose=verbose):
        await beeai_cli.commands.platform.delete(verbose=verbose)
        await run_command(
            ["uv", "tool", "uninstall", "beeai-cli"],
            "Uninstalling beeai-cli",
            env={"PATH": _path()},
        )
        console.success("BeeAI uninstalled successfully.")
