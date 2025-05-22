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

import json
import subprocess
import pathlib
import os
import sys
from typing import Optional, List
import base64
import typing

import typer
import kr8s.asyncio
import kr8s.asyncio.objects
import yaml

from beeai_cli import Configuration
from beeai_cli.async_typer import AsyncTyper, console
from beeai_cli.utils import get_telemetry_config

app = AsyncTyper()

configuration = Configuration()

DATA = pathlib.Path(__file__).joinpath("../../../../data").resolve()
LIMA_HOME = configuration.home / "lima"
KUBECONFIG = LIMA_HOME / "beeai" / "copied-from-guest" / "kubeconfig.yaml"

HelmChart = kr8s.asyncio.objects.new_class(
    kind="HelmChart",
    version="helm.cattle.io/v1",
    namespaced=True,
)


def _run_command(
    cmd: List[str],
    message: str,
    env: dict = {},
    cwd: str = ".",
) -> subprocess.CompletedProcess:
    """Helper function to run a subprocess command and handle common errors."""
    try:
        with console.status(message + "...", spinner="dots"):
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                env={**os.environ, **env},
                cwd=cwd,
            )
    except FileNotFoundError:
        tool_name = cmd[0]
        console.print(f"[red]Error: {tool_name} is not installed. Please install {tool_name} first.[/red]")
        if tool_name == "limactl":
            console.print("[yellow]You can install Lima with: brew install lima[/yellow]")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]ERROR: '{message}' failed with exit code {e.returncode}[/red]")
        if e.stderr:
            console.print(f"[red]Error: {e.stderr.strip()}[/red]")
        if e.stdout:
            console.print(f"[red]Output: {e.stdout.strip()}[/red]")
        sys.exit(1)


async def _get_lima_instance() -> Optional[dict]:
    result = _run_command(
        ["limactl", "--tty=false", "list", "--format=json"],
        "Looking for existing BeeAI VM",
        env={"LIMA_HOME": str(LIMA_HOME)},
    )

    return next(
        (
            instance
            for line in result.stdout.split("\n")
            if line
            if (instance := json.loads(line))
            if instance.get("name") == "beeai"
        ),
        None,
    )


@app.command("start")
async def start(
    set_values_list: typing.Annotated[
        list[str],
        typer.Option(
            "--set",
            hidden=True,
            help="Set Helm chart values using <key>=<value> syntax, like: --set image.tag=local",
            default_factory=list,
        ),
    ],
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "beeai",
    import_images: typing.Annotated[
        bool, typer.Option(hidden=True, help="Load images from the ~/.beeai/images folder on host into the VM")
    ] = False,
):
    """Start BeeAI platform."""
    configuration.home.mkdir(exist_ok=True)
    lima_instance = await _get_lima_instance()

    if not lima_instance:
        LIMA_HOME.mkdir(parents=True, exist_ok=True)
        _run_command(
            [
                "limactl",
                "--tty=false",
                "start",
                DATA / "lima-vm.yaml",
                f"--name={vm_name}",
            ],
            "Creating BeeAI VM",
            env={"LIMA_HOME": str(LIMA_HOME)},
        )
    elif lima_instance.get("status") != "Running":
        _run_command(
            ["limactl", "--tty=false", "start", vm_name],
            "Starting BeeAI VM",
            env={"LIMA_HOME": str(LIMA_HOME)},
        )
    else:
        console.print("BeeAI VM is already running.")

    _run_command(
        ["limactl", "--tty=false", "start-at-login", vm_name],
        "Configuring BeeAI VM",
        env={"LIMA_HOME": str(LIMA_HOME)},
    )

    if import_images:
        _run_command(
            [
                "limactl",
                "--tty=false",
                "shell",
                vm_name,
                "--",
                "/bin/bash",
                "-c",
                "sudo ctr images import /beeai/images/*",
            ],
            "Importing images",
            env={"LIMA_HOME": str(LIMA_HOME)},
            cwd="/",
        )

    values = {
        "externalRegistries": {
            "public_github": "https://github.com/i-am-bee/beeai-platform@release-v0.1.3#path=agent-registry.yaml"
        },
        # This is a "dummy" value for local use only
        "encryptionKey": "Ovx8qImylfooq4-HNwOzKKDcXLZCB3c_m0JlB9eJBxc=",
        "auth": {"enabled": False},
    }

    set_values = {key: value for key, value in (value.split("=", 1) for value in set_values_list)}
    # add telemetry into set values, not values, because we can later patch it easily
    set_values["telemetry.sharing"] = str(get_telemetry_config()["sharing"]).lower()

    try:
        with console.status("Applying HelmChart to Kubernetes...", spinner="dots"):
            helm_chart = HelmChart(
                {
                    "metadata": {
                        "name": "beeai",
                        "namespace": "default",
                    },
                    "spec": {
                        "chartContent": base64.b64encode((DATA / "helm-chart.tgz").read_bytes()).decode(),
                        "targetNamespace": "beeai",
                        "createNamespace": True,
                        "valuesContent": yaml.dump(values),
                        "set": set_values,
                    },
                },
                api=await kr8s.asyncio.api(kubeconfig=KUBECONFIG),
            )
            if await helm_chart.exists():
                await helm_chart.patch(helm_chart.raw)
            else:
                await helm_chart.create()
    except Exception as e:
        console.print(f"[red]Error applying HelmChart: {e}[/red]")
        sys.exit(1)

    console.print("[green]BeeAI platform deployed successfully![/green]")


@app.command("stop")
async def stop(
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "beeai",
):
    """Stop BeeAI platform VM."""
    lima_instance = await _get_lima_instance()

    if not lima_instance:
        console.print("BeeAI VM not found. Nothing to stop.")
        return

    if lima_instance.get("status") != "Running":
        console.print(f"BeeAI VM is not running (status: {lima_instance.get('status')}). Nothing to stop.")
        return

    _run_command(
        ["limactl", "--tty=false", "stop", vm_name],
        "Stopping BeeAI VM",
        env={"LIMA_HOME": str(LIMA_HOME)},
    )
    console.print("[green]BeeAI VM stopped successfully.[/green]")


@app.command("delete")
async def delete(
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "beeai",
):
    """Delete BeeAI platform VM."""
    if not await _get_lima_instance():
        console.print("BeeAI VM not found. Nothing to delete.")
        return

    _run_command(
        ["limactl", "--tty=false", "delete", "--force", vm_name],
        "Deleting BeeAI VM",
        env={"LIMA_HOME": str(LIMA_HOME)},
    )

    console.print("[green]BeeAI VM deleted successfully.[/green]")
