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

import asyncio
import base64
import functools
import importlib.resources
import json
import os
import platform
import shutil
import sys
import typing

import anyio
import typer
import yaml

from beeai_cli.api import wait_for_api
from beeai_cli.async_typer import AsyncTyper
from beeai_cli.configuration import Configuration
from beeai_cli.console import console
from beeai_cli.utils import VMDriver, run_command, verbosity

app = AsyncTyper()

configuration = Configuration()


def _lima_yaml(k3s_port: int = 16443, beeai_port: int = 8333, phoenix_port: int = 6006) -> str:
    return rf"""
images:
- location: "https://cloud-images.ubuntu.com/releases/noble/release-20250516/ubuntu-24.04-server-cloudimg-amd64.img"
  arch: "x86_64"
  digest: "sha256:8d6161defd323d24d66f85dda40e64e2b9021aefa4ca879dcbc4ec775ad1bbc5"
- location: "https://cloud-images.ubuntu.com/releases/noble/release-20250516/ubuntu-24.04-server-cloudimg-arm64.img"
  arch: "aarch64"
  digest: "sha256:c933c6932615d26c15f6e408e4b4f8c43cb3e1f73b0a98c2efa916cc9ab9549c"
- location: https://cloud-images.ubuntu.com/releases/noble/release/ubuntu-24.04-server-cloudimg-amd64.img
  arch: x86_64
- location: https://cloud-images.ubuntu.com/releases/noble/release/ubuntu-24.04-server-cloudimg-arm64.img
  arch: aarch64

mounts:
- location: "~/.beeai"
  mountPoint: "/beeai"

containerd:
  system: false
  user: false

hostResolver:
  hosts:
    host.docker.internal: host.lima.internal

provision:
- mode: system
  script: |
    #!/bin/sh
    if [ ! -d /var/lib/rancher/k3s ]; then
      curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644 --https-listen-port={k3s_port}
    fi

probes:
- script: |
    #!/bin/bash
    set -eux -o pipefail
    if ! timeout 30s bash -c "until test -f /etc/rancher/k3s/k3s.yaml; do sleep 3; done"; then
      echo >&2 "k3s is not running yet"
      exit 1
    fi

copyToHost:
- guest: "/etc/rancher/k3s/k3s.yaml"
  host: "{{{{.Dir}}}}/copied-from-guest/kubeconfig.yaml"
  deleteOnStop: true

portForwards:
  - guestPort: 31833
    hostPort: {beeai_port}
  - guestPort: 31606
    hostPort: {phoenix_port}"""


@functools.cache
def _limactl_exe():
    bundled_limactl = importlib.resources.files("beeai_cli") / "data" / "limactl"
    if bundled_limactl.is_file():
        return bundled_limactl
    else:
        limactl = shutil.which("limactl")
        console.print(
            f"[yellow]Warning: Using external Lima from {limactl}. This is fine in development, as long as the version matches.[/yellow]"
        )
        return limactl


def _validate_driver(vm_driver: VMDriver | None) -> VMDriver:
    is_windows = platform.system() == "Windows" or shutil.which("wsl.exe")
    has_lima = (importlib.resources.files("beeai_cli") / "data" / "limactl").is_file() or shutil.which("limactl")
    has_docker = shutil.which("docker")
    has_vz = os.path.exists("/System/Library/Frameworks/Virtualization.framework")
    has_qemu = bool(
        shutil.which(
            {"x86_64": "qemu-system-x86_64", "arm64": "qemu-system-aarch64", "aarch64": "qemu-system-aarch64"}[
                platform.machine()
            ]
        )
    )
    match vm_driver:
        case None:
            if is_windows:
                if has_docker:
                    return VMDriver.docker
                else:
                    console.print(
                        "[red]Error: Running on Windows, but no compatible VM runtime found. Please follow the Windows installation instructions at https://docs.beeai.dev/introduction/installation[/red]"
                    )
                    sys.exit(1)
            # macOS / Linux
            if has_lima and (has_vz or has_qemu):
                return VMDriver.lima
            elif has_docker:
                return VMDriver.docker
            else:
                console.print(
                    "[red]Error: Could not find a compatible VM runtime. Please follow the installation instructions at https://docs.beeai.dev/introduction/installation[/red]"
                )
                sys.exit(1)
        case VMDriver.lima:
            if not has_lima:
                console.print(
                    "[red]Error: Lima not found. Please follow the installation instructions at https://docs.beeai.dev/introduction/installation[/red]"
                )
                sys.exit(1)
            if not has_vz and not has_qemu:
                console.print(
                    "[red]Error: QEMU not found. Please follow the installation instructions at https://docs.beeai.dev/introduction/installation[/red]"
                )
                sys.exit(1)
        case VMDriver.docker:
            if not has_docker:
                console.print(
                    "[red]Error: Docker not found. Please follow the installation instructions at https://docs.beeai.dev/introduction/installation[/red]"
                )
                sys.exit(1)
    return vm_driver


async def _get_platform_status(vm_driver: VMDriver, vm_name: str) -> str | None:
    try:
        match vm_driver:
            case VMDriver.lima:
                result = await run_command(
                    [_limactl_exe(), "--tty=false", "list", "--format=json"],
                    f"Looking for existing instance in {vm_driver.name.capitalize()}",
                    env={"LIMA_HOME": str(configuration.lima_home)},
                )
                return next(
                    (
                        status["status"].lower() if "status" in status else None
                        for line in result.stdout.decode().split("\n")
                        if line
                        if (status := json.loads(line))
                        if status.get("name") == vm_name
                    ),
                    None,
                )
            case VMDriver.docker:
                result = await run_command(
                    ["docker", "inspect", vm_name],
                    "Looking for existing BeeAI platform",
                    check=False,
                )
                return json.loads(result.stdout)[0]["State"]["Status"].lower()
    except Exception:
        return None


@app.command("start")
async def start(
    set_values_list: typing.Annotated[
        list[str],
        typer.Option(
            "--set",
            help="Set Helm chart values using <key>=<value> syntax, like: --set image.tag=local",
            default_factory=list,
        ),
    ],
    import_images: typing.Annotated[
        list[str],
        typer.Option(
            "--import",
            help="Import an image from a local Docker CLI into BeeAI platform",
            default_factory=list,
        ),
    ],
    telemetry_sharing: typing.Annotated[
        bool, typer.Option(help="Control the sharing of telemetry data with the BeeAI team")
    ] = True,
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "beeai-platform",
    vm_driver: typing.Annotated[
        VMDriver | None, typer.Option(hidden=True, help="Platform driver: lima (VM) or docker (container)")
    ] = None,
    k3s_port: typing.Annotated[int, typer.Option(hidden=True)] = 16443,
    beeai_port: typing.Annotated[int, typer.Option(hidden=True)] = 8333,
    phoenix_port: typing.Annotated[int, typer.Option(hidden=True)] = 6006,
    verbose: typing.Annotated[bool, typer.Option("-v", help="Show verbose output")] = False,
):
    """Start BeeAI platform."""
    with verbosity(verbose):
        vm_driver = _validate_driver(vm_driver)

        # Clean up legacy Brew services
        await run_command(
            ["brew", "services", "stop", "beeai"],
            "Cleaning up legacy BeeAI service",
            check=False,
            ignore_missing=True,
        )
        await run_command(
            ["brew", "services", "stop", "arize-phoenix"],
            "Cleaning up legacy Arize Phoenix service",
            check=False,
            ignore_missing=True,
        )

        # Start VM
        configuration.home.mkdir(exist_ok=True)
        status = await _get_platform_status(vm_driver, vm_name)
        if not status:
            await run_command(
                {
                    VMDriver.lima: [_limactl_exe(), "--tty=false", "delete", "--force", vm_name],
                    VMDriver.docker: ["docker", "rm", "--force", vm_name],
                }[vm_driver],
                "Cleaning up remains of previous instance",
                env={"LIMA_HOME": str(configuration.lima_home)},
                check=False,
            )
            templates_dir = configuration.lima_home / "_templates"
            if vm_driver == VMDriver.lima:
                templates_dir.mkdir(parents=True, exist_ok=True)
                templates_dir.joinpath(f"{vm_name}.yaml").write_text(
                    _lima_yaml(k3s_port=k3s_port, beeai_port=beeai_port, phoenix_port=phoenix_port)
                )
            await run_command(
                {
                    VMDriver.lima: [
                        _limactl_exe(),
                        "--tty=false",
                        "start",
                        templates_dir / f"{vm_name}.yaml",
                        f"--name={vm_name}",
                    ],
                    VMDriver.docker: [
                        "docker",
                        "run",
                        "--privileged",
                        f"--name={vm_name}",
                        f"--hostname={vm_name}",
                        "-p",
                        f"{k3s_port}:{k3s_port}",
                        "-p",
                        f"{beeai_port}:31833",
                        "-p",
                        f"{phoenix_port}:31606",
                        "-v",
                        f"{configuration.home}:/beeai",
                        "-d",
                        "rancher/k3s:v1.33.0-k3s1",
                        "--",
                        "server",
                        "--write-kubeconfig-mode=644",
                        f"--https-listen-port={k3s_port}",
                    ],
                }[vm_driver],
                "Creating a " + {VMDriver.lima: "Lima VM", VMDriver.docker: "Docker container"}[vm_driver],
                env={
                    "LIMA_HOME": str(configuration.lima_home),
                    # Hotfix for port-forwarding until this issue is resolved:
                    # https://github.com/lima-vm/lima/issues/3601#issuecomment-2936952923
                    "LIMA_SSH_PORT_FORWARDER": "true",
                },
            )
        elif status != "running":
            await run_command(
                {
                    VMDriver.lima: [_limactl_exe(), "--tty=false", "start", vm_name],
                    VMDriver.docker: ["docker", "start", vm_name],
                }[vm_driver],
                "Starting up",
                env={
                    "LIMA_HOME": str(configuration.lima_home),
                    # Hotfix for port-forwarding until this issue is resolved:
                    # https://github.com/lima-vm/lima/issues/3601#issuecomment-2936952923
                    "LIMA_SSH_PORT_FORWARDER": "true",
                },
            )
        else:
            console.print("Updating an existing instance.")

        if vm_driver == VMDriver.lima:
            await run_command(
                [
                    "limactl",
                    "--tty=false",
                    "start-at-login",
                    # TODO: temporarily disabled due to port-forwarding issue (workaround not working in start-at-login)
                    "--enabled=false",
                    vm_name,
                ],
                "Configuring",
                env={
                    "LIMA_HOME": str(configuration.lima_home),
                    # Hotfix for port-forwarding until this issue is resolved:
                    # https://github.com/lima-vm/lima/issues/3601#issuecomment-2936952923
                    "LIMA_SSH_PORT_FORWARDER": "true",
                },
            )

        if vm_driver == VMDriver.docker:
            for _ in range(10):
                with console.status("Waiting for k3s to start...", spinner="dots"):
                    await asyncio.sleep(5)
                if (
                    await run_command(
                        ["docker", "exec", vm_name, "kubectl", "get", "crd", "helmcharts.helm.cattle.io"],
                        message="Checking if k3s is running",
                        check=False,
                    )
                ).returncode == 0:
                    break
            else:
                console.print("[red]Error: Timed out waiting for k3s to start.[/red]")
                sys.exit(1)

        # Import images
        for image in import_images:
            await import_image(image, vm_name=vm_name, vm_driver=vm_driver)

        # Deploy HelmChart
        await run_command(
            [
                *{
                    VMDriver.lima: [_limactl_exe(), "shell", vm_name, "--"],
                    VMDriver.docker: ["docker", "exec", "-i", vm_name],
                }[vm_driver],
                "kubectl",
                "apply",
                "-f",
                "-",
            ],
            "Applying Helm chart",
            input=yaml.dump(
                {
                    "apiVersion": "helm.cattle.io/v1",
                    "kind": "HelmChart",
                    "metadata": {
                        "name": "beeai",
                        "namespace": "default",
                    },
                    "spec": {
                        "chartContent": base64.b64encode(
                            (importlib.resources.files("beeai_cli") / "data" / "helm-chart.tgz").read_bytes()
                        ).decode(),
                        "targetNamespace": "default",
                        "valuesContent": yaml.dump(
                            {
                                "externalRegistries": {"public_github": str(configuration.agent_registry)},
                                "encryptionKey": "Ovx8qImylfooq4-HNwOzKKDcXLZCB3c_m0JlB9eJBxc=",  # Dummy key for local use
                                "features": {"uiNavigation": True},
                                "auth": {"enabled": False},
                                "telemetry": {"sharing": telemetry_sharing},
                            }
                        ),
                        "set": dict(value.split("=", 1) for value in set_values_list),
                    },
                }
            ).encode("utf-8"),
            env={"LIMA_HOME": str(configuration.lima_home)},
            cwd="/",
        )

        with console.status("Waiting for BeeAI platform to be ready...", spinner="dots"):
            await wait_for_api()

        console.print("[green]BeeAI platform started successfully![/green]")


@app.command("stop")
async def stop(
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "beeai-platform",
    vm_driver: typing.Annotated[
        VMDriver | None, typer.Option(hidden=True, help="Platform driver: lima (VM) or docker (container)")
    ] = None,
    verbose: typing.Annotated[bool, typer.Option("-v", help="Show verbose output")] = False,
):
    """Stop BeeAI platform."""
    with verbosity(verbose):
        vm_driver = _validate_driver(vm_driver)
        status = await _get_platform_status(vm_driver, vm_name)
        if not status:
            console.print("BeeAI platform not found. Nothing to stop.")
            return
        await run_command(
            {
                VMDriver.lima: [_limactl_exe(), "--tty=false", "stop", "--force", vm_name],
                VMDriver.docker: ["docker", "stop", vm_name],
            }[vm_driver],
            "Stopping BeeAI VM",
            env={"LIMA_HOME": str(configuration.lima_home)},
        )
        console.print("[green]BeeAI platform stopped successfully.[/green]")


@app.command("delete")
async def delete(
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "beeai-platform",
    vm_driver: typing.Annotated[
        VMDriver | None, typer.Option(hidden=True, help="Platform driver: lima (VM) or docker (container)")
    ] = None,
    verbose: typing.Annotated[bool, typer.Option("-v", help="Show verbose output")] = False,
):
    """Delete BeeAI platform."""
    with verbosity(verbose):
        vm_driver = _validate_driver(vm_driver)
        await run_command(
            {
                VMDriver.lima: [_limactl_exe(), "--tty=false", "delete", "--force", vm_name],
                VMDriver.docker: ["docker", "rm", "--force", vm_name],
            }[vm_driver],
            "Deleting BeeAI platform",
            env={"LIMA_HOME": str(configuration.lima_home)},
            check=False,
        )
        console.print("[green]BeeAI platform deleted successfully.[/green]")


@app.command("import")
async def import_image(
    tag: typing.Annotated[str, typer.Argument(help="Docker image tag to import")],
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "beeai-platform",
    vm_driver: typing.Annotated[
        VMDriver | None, typer.Option(hidden=True, help="Platform driver: lima (VM) or docker (container)")
    ] = None,
    verbose: typing.Annotated[bool, typer.Option("-v", help="Show verbose output")] = False,
):
    """Import a local docker image into the BeeAI platform."""
    with verbosity(verbose):
        vm_driver = _validate_driver(vm_driver)
        await run_command(["bash", "-c", "rm -f ~/.beeai/images/*"], "Removing temporary files")
        image_path = Configuration().home / "images" / (tag.replace("/", "_") + ".tar")
        image_path.parent.mkdir(parents=True, exist_ok=True)

        status = await _get_platform_status(vm_driver, vm_name)
        if status != "running":
            raise RuntimeError("BeeAI platform is not running. Start the platform first before importing images.")

        await run_command(
            ["docker", "image", "save", "-o", str(image_path), tag],
            "Exporting images from Docker",
        )
        await run_command(
            {
                VMDriver.lima: [_limactl_exe(), "--tty=false", "shell", vm_name, "--"],
                VMDriver.docker: ["docker", "exec", vm_name],
            }[vm_driver]
            + [
                "/bin/sh",
                "-c",
                f'for img in /beeai/images/*; do {"sudo" if vm_driver == VMDriver.lima else ""} ctr images import "$img"; done',
            ],
            "Importing images into BeeAI platform",
            env={"LIMA_HOME": str(Configuration().lima_home)},
            cwd="/",
        )
        await run_command(["/bin/sh", "-c", "rm -f ~/.beeai/images/*"], "Removing temporary files")


@app.command("exec")
async def exec(
    command: typing.Annotated[list[str] | None, typer.Argument()] = None,
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "beeai-platform",
    vm_driver: typing.Annotated[
        VMDriver | None, typer.Option(hidden=True, help="Platform driver: lima (VM) or docker (container)")
    ] = None,
):
    """For debugging -- execute a command inside the BeeAI platform VM."""
    command = command or ["/bin/sh"]
    vm_driver = _validate_driver(vm_driver)
    status = await _get_platform_status(vm_driver, vm_name)
    if status != "running":
        console.log("[red]BeeAI platform is not running.[/red]")
        sys.exit(1)
    await anyio.run_process(
        [
            *{
                VMDriver.lima: [_limactl_exe(), "shell", f"--tty={sys.stdin.isatty()}", vm_name, "--"],
                VMDriver.docker: ["docker", "exec", "-it" if sys.stdin.isatty() else "-i", vm_name],
            }[vm_driver],
            *command,
        ],
        input=None if sys.stdin.isatty() else sys.stdin.read(),
        check=False,
        stdout=None,
        stderr=None,
        env={**os.environ, "LIMA_HOME": str(configuration.lima_home)},
        cwd="/",
    )
