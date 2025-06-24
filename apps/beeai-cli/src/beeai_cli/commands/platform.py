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
import configparser
import functools
import importlib.resources
import json
import os
import pathlib
import platform
import shutil
import sys
import textwrap
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


@functools.cache
def _limactl_exe():
    bundled_limactl = importlib.resources.files("beeai_cli") / "data" / "limactl"
    if bundled_limactl.is_file():
        return bundled_limactl
    else:
        return shutil.which("limactl")


async def _validate_driver(vm_driver: VMDriver | None) -> VMDriver:
    is_windows = platform.system() == "Windows"
    has_lima = (importlib.resources.files("beeai_cli") / "data" / "limactl").is_file() or shutil.which("limactl")
    has_docker = shutil.which("docker")
    has_vz = os.path.exists("/System/Library/Frameworks/Virtualization.framework")
    arch = platform.machine().lower()
    has_qemu = not is_windows and bool(shutil.which("qemu-system-" + ("aarch64" if arch == "arm64" else arch)))

    if not is_windows and shutil.which("wsl.exe"):
        console.print(
            "[red]Error: BeeAI CLI does not support running inside WSL. Please run it in Windows directly, according to the installation instructions at https://docs.beeai.dev/introduction/installation[/red]"
        )
        sys.exit(1)

    match vm_driver:
        case None:
            if is_windows:
                vm_driver = VMDriver.wsl
            elif has_lima and (has_vz or has_qemu):
                vm_driver = VMDriver.lima
            elif has_docker:
                console.print(
                    "[yellow]Warning: Running the VM in Docker, since Lima is not set up properly. If you want to use Lima instead, run `beeai platform delete --vm-driver=docker` and then follow the installation instructions at https://docs.beeai.dev/introduction/installation[/yellow]"
                )
                vm_driver = VMDriver.docker
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
        case VMDriver.wsl:
            if not is_windows:
                console.print(
                    "[red]Error: WSL is only supported on Windows. Please follow the installation instructions at https://docs.beeai.dev/introduction/installation[/red]"
                )
                sys.exit(1)

    if vm_driver == VMDriver.lima and not (importlib.resources.files("beeai_cli") / "data" / "limactl").is_file():
        console.print(
            f"[yellow]Warning: Using external Lima from {shutil.which('limactl')}. This is fine in development, as long as the version matches.[/yellow]"
        )

    if (
        vm_driver == VMDriver.wsl
        and (
            await run_command(
                ["net.exe", "session"],
                "Checking for admin rights",
                check=False,
            )
        ).returncode
        != 0
    ):
        console.print(
            "[red]Error: This command must be executed as administrator. TIP: Press Win+X to show a menu where you can open a new terminal as administrator.[/red]"
        )
        sys.exit(0)

    return vm_driver


async def _get_platform_status(vm_driver: VMDriver, vm_name: str) -> str | None:
    try:
        match vm_driver:
            case VMDriver.lima:
                result = await run_command(
                    [_limactl_exe(), "--tty=false", "list", "--format=json"],
                    f"Looking for existing instance in {vm_driver.name.capitalize()}",
                    env={"LIMA_HOME": str(Configuration().lima_home)},
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
            case VMDriver.wsl:
                running = (
                    (
                        await run_command(
                            ["wsl.exe", "--list", "--running", "--quiet"],
                            "Looking for running BeeAI platform",
                            env={"WSL_UTF8": "1"},
                        )
                    )
                    .stdout.decode()
                    .splitlines()
                )
                if vm_name in running:
                    return "running"
                installed = (
                    (
                        await run_command(
                            ["wsl.exe", "--list", "--quiet"],
                            "Looking for existing BeeAI platform",
                            env={"WSL_UTF8": "1"},
                        )
                    )
                    .stdout.decode()
                    .splitlines()
                )
                if vm_name in installed:
                    return "stopped"
                return None
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
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "beeai-platform",
    vm_driver: typing.Annotated[
        VMDriver | None, typer.Option(hidden=True, help="Platform driver: lima (VM) or docker (container)")
    ] = None,
    verbose: typing.Annotated[bool, typer.Option("-v", help="Show verbose output")] = False,
):
    """Start BeeAI platform."""
    with verbosity(verbose):
        vm_driver = await _validate_driver(vm_driver)

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

        if vm_driver == VMDriver.wsl:
            # Install WSL2
            if (await run_command(["wsl.exe", "--status"], "Checking for WSL2", check=False)).returncode != 0 or not (
                await run_command(
                    ["wsl.exe", "--list", "--quiet"],
                    "Checking for WSL2 distributions",
                    env={"WSL_UTF8": "1"},
                )
            ).stdout.decode().strip():
                await run_command(["wsl.exe", "--install", "--no-launch", "--web-download"], "Installing WSL2")

            # Upgrade WSL2
            await run_command(["wsl.exe", "--upgrade"], "Upgrading WSL2", check=False)

            # Configure networking mode
            # (NAT is the default, but we originally told users to switch to mirrored, so we just configure it back)
            config_file_path = pathlib.Path.home().joinpath(".wslconfig")
            config_file_path.touch()
            config = configparser.ConfigParser()
            with config_file_path.open("r+") as f:
                config.read(f)
                if not config.has_section("wsl2"):
                    config.add_section("wsl2")
                if config.get("wsl2", "networkingMode", fallback=None) != "NAT":
                    config.set("wsl2", "networkingMode", "NAT")
                    f.seek(0)
                    f.truncate(0)
                    config.write(f)
                    await run_command(["wsl.exe", "--shutdown"], "Updating WSL2 networking")

        # Start VM
        Configuration().home.mkdir(exist_ok=True)
        status = await _get_platform_status(vm_driver, vm_name)
        if not status:
            await run_command(
                {
                    VMDriver.lima: [_limactl_exe(), "--tty=false", "delete", "--force", vm_name],
                    VMDriver.docker: ["docker", "rm", "--force", vm_name],
                    VMDriver.wsl: ["wsl.exe", "--unregister", vm_name],
                }[vm_driver],
                "Cleaning up remains of previous instance",
                env={"LIMA_HOME": str(Configuration().lima_home)},
                check=False,
            )
            templates_dir = Configuration().lima_home / "_templates"
            if vm_driver == VMDriver.lima:
                templates_dir.mkdir(parents=True, exist_ok=True)
                templates_dir.joinpath(f"{vm_name}.yaml").write_text(
                    yaml.dump(
                        {
                            "images": [
                                {
                                    "location": "https://cloud-images.ubuntu.com/releases/noble/release-20250516/ubuntu-24.04-server-cloudimg-amd64.img",
                                    "arch": "x86_64",
                                    "digest": "sha256:8d6161defd323d24d66f85dda40e64e2b9021aefa4ca879dcbc4ec775ad1bbc5",
                                },
                                {
                                    "location": "https://cloud-images.ubuntu.com/releases/noble/release-20250516/ubuntu-24.04-server-cloudimg-arm64.img",
                                    "arch": "aarch64",
                                    "digest": "sha256:c933c6932615d26c15f6e408e4b4f8c43cb3e1f73b0a98c2efa916cc9ab9549c",
                                },
                                {
                                    "location": "https://cloud-images.ubuntu.com/releases/noble/release/ubuntu-24.04-server-cloudimg-amd64.img",
                                    "arch": "x86_64",
                                },
                                {
                                    "location": "https://cloud-images.ubuntu.com/releases/noble/release/ubuntu-24.04-server-cloudimg-arm64.img",
                                    "arch": "aarch64",
                                },
                            ],
                            "mounts": [
                                {
                                    "location": "~/.beeai",
                                    "mountPoint": "/beeai",
                                }
                            ],
                            "containerd": {
                                "system": False,
                                "user": False,
                            },
                            "hostResolver": {"hosts": {"host.docker.internal": "host.lima.internal"}},
                            "provision": [
                                {
                                    "mode": "system",
                                    "script": (
                                        "#!/bin/sh\n"
                                        "if [ ! -d /var/lib/rancher/k3s ]; then curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644 --https-listen-port=16443; fi"
                                    ),
                                }
                            ],
                            "probes": [
                                {
                                    "script": (
                                        "#!/bin/bash\n"
                                        "set -eux -o pipefail\n"
                                        'if ! timeout 30s bash -c "until test -f /etc/rancher/k3s/k3s.yaml; do sleep 3; done"; then echo >&2 "k3s is not running yet"; exit 1; fi\n'
                                    )
                                }
                            ],
                            "copyToHost": [
                                {
                                    "guest": "/etc/rancher/k3s/k3s.yaml",
                                    "host": "{{.Dir}}/copied-from-guest/kubeconfig.yaml",
                                    "deleteOnStop": True,
                                }
                            ],
                            "portForwards": [
                                {"guestPort": 31833, "hostPort": 8333},
                                {"guestPort": 31606, "hostPort": 6006},
                            ],
                        }
                    )
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
                        "16433:16433",
                        "-p",
                        "8333:31833",
                        "-p",
                        "6006:31606",
                        "-v",
                        f"{Configuration().home}:/beeai",
                        "-d",
                        "rancher/k3s:v1.33.0-k3s1",
                        "--",
                        "server",
                        "--write-kubeconfig-mode=644",
                        "--https-listen-port=16433",
                    ],
                    VMDriver.wsl: [
                        "wsl.exe",
                        "--install",
                        "--name",
                        vm_name,
                        "--no-launch",
                        "--web-download",
                    ],
                }[vm_driver],
                "Creating a "
                + {VMDriver.lima: "Lima VM", VMDriver.docker: "Docker container", VMDriver.wsl: "WSL distribution"}[
                    vm_driver
                ],
                env={
                    "LIMA_HOME": str(Configuration().lima_home),
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
                    VMDriver.wsl: ["wsl.exe", "--user", "root", "--distribution", vm_name, "dbus-launch", "true"],
                }[vm_driver],
                "Starting up",
                env={
                    "LIMA_HOME": str(Configuration().lima_home),
                    # Hotfix for port-forwarding until this issue is resolved:
                    # https://github.com/lima-vm/lima/issues/3601#issuecomment-2936952923
                    "LIMA_SSH_PORT_FORWARDER": "true",
                },
            )
        else:
            console.print("Updating an existing instance.")

        # Configure start-at-login for Lima
        if vm_driver == VMDriver.lima:
            await run_command(
                [
                    _limactl_exe(),
                    "--tty=false",
                    "start-at-login",
                    # TODO: temporarily disabled due to port-forwarding issue (workaround not working in start-at-login)
                    "--enabled=false",
                    vm_name,
                ],
                "Disabling start-at-login",
                env={
                    "LIMA_HOME": str(Configuration().lima_home),
                    # Hotfix for port-forwarding until this issue is resolved:
                    # https://github.com/lima-vm/lima/issues/3601#issuecomment-2936952923
                    "LIMA_SSH_PORT_FORWARDER": "true",
                },
            )

        # Wait for asynchronous k3s startup for Docker
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

        # Set up WSL
        if vm_driver == VMDriver.wsl:
            # Run a persistent process
            await run_command(
                ["wsl.exe", "--user", "root", "--distribution", vm_name, "--", "dbus-launch", "true"],
                message="Ensuring persistence of WSL2",
            )

            # Install k3s
            await run_command(
                [
                    "wsl.exe",
                    "--user",
                    "root",
                    "--distribution",
                    vm_name,
                    "--",
                    "sh",
                    "-c",
                    "curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644 --https-listen-port=16433",
                ],
                message="Installing k3s",
            )

            # Set-up host.docker.internal
            host_ip = next(
                line.split()[2]
                for line in (
                    await run_command(
                        ["wsl.exe", "--user", "root", "--distribution", vm_name, "--", "ip", "route", "show"],
                        "Detecting host IP address",
                        env={"WSL_UTF8": "1"},
                    )
                )
                .stdout.decode()
                .strip()
                .splitlines()
                if line.startswith("default via ")
            )
            await run_command(
                ["wsl.exe", "--user", "root", "--distribution", vm_name, "--", "kubectl", "apply", "-f", "-"],
                "Setting up internal networking",
                input=yaml.dump(
                    {
                        "apiVersion": "v1",
                        "kind": "ConfigMap",
                        "metadata": {
                            "name": "coredns-custom",
                            "namespace": "kube-system",
                        },
                        "data": {
                            "default.server": textwrap.dedent(
                                f"""\
                                host.docker.internal {{
                                    hosts {{
                                        {host_ip} host.docker.internal
                                        fallthrough
                                    }}
                                }}
                                """
                            )
                        },
                    }
                ).encode(),
            )

            # Start port-forwarding to Windows
            guest_ip = (
                (
                    await run_command(
                        ["wsl.exe", "--user", "root", "--distribution", vm_name, "--", "hostname", "-I"],
                        "Detecting VM IP address",
                        env={"WSL_UTF8": "1"},
                    )
                )
                .stdout.decode()
                .strip()
                .split()[0]
            )
            await run_command(
                [
                    "netsh.exe",
                    "interface",
                    "portproxy",
                    "add",
                    "v4tov4",
                    "listenport=8333",
                    "listenaddress=0.0.0.0",
                    "connectport=31833",
                    f"connectaddress={guest_ip}",
                ],
                "Forwarding the BeeAI port",
                check=False,
            )
            await run_command(
                [
                    "netsh.exe",
                    "interface",
                    "portproxy",
                    "add",
                    "v4tov4",
                    "listenport=6006",
                    "listenaddress=0.0.0.0",
                    "connectport=31606",
                    f"connectaddress={guest_ip}",
                ],
                "Forwarding the Arize Phoenix port",
                check=False,
            )

        # Import images
        for image in import_images:
            await import_image(image, vm_name=vm_name, vm_driver=vm_driver)

        # Deploy HelmChart
        await run_command(
            [
                *{
                    VMDriver.lima: [_limactl_exe(), "shell", vm_name, "--"],
                    VMDriver.docker: ["docker", "exec", "-i", vm_name],
                    VMDriver.wsl: ["wsl.exe", "--user", "root", "--distribution", vm_name, "--"],
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
                        "timeout": "1h",
                        "chartContent": base64.b64encode(
                            (importlib.resources.files("beeai_cli") / "data" / "helm-chart.tgz").read_bytes()
                        ).decode(),
                        "targetNamespace": "default",
                        "valuesContent": yaml.dump(
                            {
                                "externalRegistries": {"public_github": str(Configuration().agent_registry)},
                                "encryptionKey": "Ovx8qImylfooq4-HNwOzKKDcXLZCB3c_m0JlB9eJBxc=",  # Dummy key for local use
                                "features": {"uiNavigation": True},
                                "auth": {"enabled": False},
                            }
                        ),
                        "set": dict(value.split("=", 1) for value in set_values_list),
                    },
                }
            ).encode("utf-8"),
            env={"LIMA_HOME": str(Configuration().lima_home)},
            cwd="/",
        )

        await run_command(
            [
                *{
                    VMDriver.lima: [_limactl_exe(), "shell", "--tty=false", vm_name, "--"],
                    VMDriver.docker: ["docker", "exec", "-i", vm_name],
                    VMDriver.wsl: ["wsl.exe", "--user", "root", "--distribution", vm_name, "--"],
                }[vm_driver],
                "kubectl",
                "wait",
                "--for=condition=JobCreated",
                "helmchart.helm.cattle.io/beeai",
            ],
            "Waiting for deploy job to be created",
            env={"LIMA_HOME": str(Configuration().lima_home)},
            cwd="/",
        )

        await run_command(
            [
                *{
                    VMDriver.lima: [_limactl_exe(), "shell", "--tty=false", vm_name, "--"],
                    VMDriver.docker: ["docker", "exec", "-i", vm_name],
                    VMDriver.wsl: ["wsl.exe", "--user", "root", "--distribution", vm_name, "--"],
                }[vm_driver],
                "kubectl",
                "wait",
                "--for=condition=Complete",
                "--timeout=1h",
                "job/helm-install-beeai",
            ],
            "Waiting for deploy job to be finished",
            env={"LIMA_HOME": str(Configuration().lima_home)},
            cwd="/",
        )

        await run_command(
            [
                *{
                    VMDriver.lima: [_limactl_exe(), "shell", "--tty=false", vm_name, "--"],
                    VMDriver.docker: ["docker", "exec", "-i", vm_name],
                    VMDriver.wsl: ["wsl.exe", "--user", "root", "--distribution", vm_name, "--"],
                }[vm_driver],
                "kubectl",
                "wait",
                "--for=condition=Available",
                "--timeout=1h",
                "--all",
                "deployment",
            ],
            "Waiting for deployments to be available",
            env={"LIMA_HOME": str(Configuration().lima_home)},
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
        vm_driver = await _validate_driver(vm_driver)
        status = await _get_platform_status(vm_driver, vm_name)
        if not status:
            console.print("BeeAI platform not found. Nothing to stop.")
            return
        await run_command(
            {
                VMDriver.lima: [_limactl_exe(), "--tty=false", "stop", "--force", vm_name],
                VMDriver.docker: ["docker", "stop", vm_name],
                VMDriver.wsl: ["wsl.exe", "--terminate", vm_name],
            }[vm_driver],
            "Stopping BeeAI VM",
            env={"LIMA_HOME": str(Configuration().lima_home)},
        )
        if vm_driver == VMDriver.wsl:
            await run_command(
                [
                    "netsh.exe",
                    "interface",
                    "portproxy",
                    "add",
                    "v4tov4",
                    "listenport=8333",
                    "listenaddress=0.0.0.0",
                ],
                "Un-forwarding the BeeAI port",
                check=False,
            )
            await run_command(
                [
                    "netsh.exe",
                    "interface",
                    "portproxy",
                    "add",
                    "v4tov4",
                    "listenport=6006",
                    "listenaddress=0.0.0.0",
                ],
                "Un-forwarding the Arize Phoenix port",
                check=False,
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
        vm_driver = await _validate_driver(vm_driver)
        await run_command(
            {
                VMDriver.lima: [_limactl_exe(), "--tty=false", "delete", "--force", vm_name],
                VMDriver.docker: ["docker", "rm", "--force", vm_name],
                VMDriver.wsl: ["wsl.exe", "--unregister", vm_name],
            }[vm_driver],
            "Deleting BeeAI platform",
            env={"LIMA_HOME": str(Configuration().lima_home)},
            check=False,
        )
        if vm_driver == VMDriver.wsl:
            await run_command(
                [
                    "netsh.exe",
                    "interface",
                    "portproxy",
                    "delete",
                    "v4tov4",
                    "listenport=8333",
                    "listenaddress=0.0.0.0",
                ],
                "Un-forwarding the BeeAI port",
                check=False,
            )
            await run_command(
                [
                    "netsh.exe",
                    "interface",
                    "portproxy",
                    "delete",
                    "v4tov4",
                    "listenport=6006",
                    "listenaddress=0.0.0.0",
                ],
                "Un-forwarding the Arize Phoenix port",
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
        vm_driver = await _validate_driver(vm_driver)

        for image_path in Configuration().home.joinpath("images").glob("*"):
            image_path.unlink()

        image_path = Configuration().home / "images" / (tag.replace("/", "_") + ".tar")
        image_path.parent.mkdir(parents=True, exist_ok=True)

        status = await _get_platform_status(vm_driver, vm_name)
        if status != "running":
            raise RuntimeError("BeeAI platform is not running. Start the platform first before importing images.")

        await run_command(
            ["docker", "image", "save", "-o", str(image_path), tag],
            "Exporting images from Docker",
        )

        vm_image_path = (
            (
                (
                    await run_command(
                        [
                            "wsl.exe",
                            "--user",
                            "root",
                            "--distribution",
                            vm_name,
                            "--",
                            "wslpath",
                            str(image_path),
                        ],
                        "Detecting image path in WSL",
                        env={"WSL_UTF8": "1"},
                    )
                )
                .stdout.decode()
                .strip()
            )
            if vm_driver == VMDriver.wsl
            else "/beeai/images"
        )

        await run_command(
            {
                VMDriver.lima: [_limactl_exe(), "--tty=false", "shell", vm_name, "--"],
                VMDriver.docker: ["docker", "exec", vm_name],
                VMDriver.wsl: ["wsl.exe", "--user", "root", "--distribution", vm_name, "--"],
            }[vm_driver]
            + [
                "/bin/sh",
                "-c",
                f'for img in {vm_image_path}/*; do {"sudo" if vm_driver == VMDriver.lima else ""} ctr images import "$img"; done',
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
    verbose: typing.Annotated[bool, typer.Option("-v", help="Show verbose output")] = False,
):
    """For debugging -- execute a command inside the BeeAI platform VM."""
    with verbosity(verbose, show_success_status=False):
        command = command or ["/bin/sh"]
        vm_driver = await _validate_driver(vm_driver)
        status = await _get_platform_status(vm_driver, vm_name)
        if status != "running":
            console.log("[red]BeeAI platform is not running.[/red]")
            sys.exit(1)
        await anyio.run_process(
            [
                *{
                    VMDriver.lima: [_limactl_exe(), "shell", f"--tty={sys.stdin.isatty()}", vm_name, "--"],
                    VMDriver.docker: ["docker", "exec", "-it" if sys.stdin.isatty() else "-i", vm_name],
                    VMDriver.wsl: ["wsl.exe", "--user", "root", "--distribution", vm_name, "--"],
                }[vm_driver],
                *command,
            ],
            input=None if sys.stdin.isatty() else sys.stdin.read(),
            check=False,
            stdout=None,
            stderr=None,
            env={**os.environ, "LIMA_HOME": str(Configuration().lima_home)},
            cwd="/",
        )
