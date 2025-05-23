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
import pathlib
import sys
from typing import Optional
import base64
import typing

import typer
import kr8s.asyncio
import kr8s.asyncio.objects
import yaml

from beeai_cli import Configuration
from beeai_cli.async_typer import AsyncTyper, console
from beeai_cli.utils import run_command, import_images_to_vm

app = AsyncTyper()

configuration = Configuration()

DATA = pathlib.Path(__file__).joinpath("../../../../data").resolve()

HelmChart = kr8s.asyncio.objects.new_class(
    kind="HelmChart",
    version="helm.cattle.io/v1",
    namespaced=True,
)


async def _get_lima_instance(vm_name: str) -> Optional[dict]:
    result = run_command(
        ["limactl", "--tty=false", "list", "--format=json"],
        "Looking for existing BeeAI VM",
        env={"LIMA_HOME": str(configuration.lima_home)},
    )

    return next(
        (
            instance
            for line in result.stdout.split("\n")
            if line
            if (instance := json.loads(line))
            if instance.get("name") == vm_name
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
    disable_telemetry_sharing: bool = typer.Option(False, help="Disable sharing"),
):
    """Start BeeAI platform."""
    configuration.home.mkdir(exist_ok=True)
    lima_instance = await _get_lima_instance(vm_name)

    if not lima_instance:
        configuration.lima_home.mkdir(parents=True, exist_ok=True)
        run_command(
            [
                "limactl",
                "--tty=false",
                "start",
                DATA / "lima-vm.yaml",
                f"--name={vm_name}",
            ],
            "Creating BeeAI VM",
            env={"LIMA_HOME": str(configuration.lima_home)},
        )
    elif lima_instance.get("status") != "Running":
        run_command(
            ["limactl", "--tty=false", "start", vm_name],
            "Starting BeeAI VM",
            env={"LIMA_HOME": str(configuration.lima_home)},
        )
    else:
        console.print("BeeAI VM is already running.")

    run_command(
        ["limactl", "--tty=false", "start-at-login", vm_name],
        "Configuring BeeAI VM",
        env={"LIMA_HOME": str(configuration.lima_home)},
    )

    if import_images:
        import_images_to_vm(vm_name)

    values = {
        "externalRegistries": {
            "public_github": "https://github.com/i-am-bee/beeai-platform@release-v0.1.3#path=agent-registry.yaml"
        },
        # This is a "dummy" value for local use only
        "encryptionKey": "Ovx8qImylfooq4-HNwOzKKDcXLZCB3c_m0JlB9eJBxc=",
        "auth": {"enabled": False},
        "telemetry": {"sharing": not disable_telemetry_sharing},
    }

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
                        "set": {key: value for key, value in (value.split("=", 1) for value in set_values_list)},
                    },
                },
                api=await kr8s.asyncio.api(kubeconfig=configuration.get_kubeconfig(vm_name)),
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
    lima_instance = await _get_lima_instance(vm_name)

    if not lima_instance:
        console.print("BeeAI VM not found. Nothing to stop.")
        return

    if lima_instance.get("status") != "Running":
        console.print(f"BeeAI VM is not running (status: {lima_instance.get('status')}). Nothing to stop.")
        return

    run_command(
        ["limactl", "--tty=false", "stop", vm_name],
        "Stopping BeeAI VM",
        env={"LIMA_HOME": str(configuration.lima_home)},
    )
    console.print("[green]BeeAI VM stopped successfully.[/green]")


@app.command("delete")
async def delete(
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "beeai",
):
    """Delete BeeAI platform VM."""
    if not await _get_lima_instance(vm_name):
        console.print("BeeAI VM not found. Nothing to delete.")
        return

    run_command(
        ["limactl", "--tty=false", "delete", "--force", vm_name],
        "Deleting BeeAI VM",
        env={"LIMA_HOME": str(configuration.lima_home)},
    )

    console.print("[green]BeeAI VM deleted successfully.[/green]")
