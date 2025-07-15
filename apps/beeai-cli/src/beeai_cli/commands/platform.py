# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

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
import uuid

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


@functools.cache
def _vm_driver() -> VMDriver:
    is_windows = platform.system() == "Windows" or shutil.which("wsl.exe")
    has_lima = (importlib.resources.files("beeai_cli") / "data" / "limactl").is_file() or shutil.which("limactl")
    has_vz = os.path.exists("/System/Library/Frameworks/Virtualization.framework")
    arch = platform.machine().lower()
    has_qemu = not is_windows and bool(shutil.which("qemu-system-" + ("aarch64" if arch == "arm64" else arch)))

    if is_windows:
        vm_driver = VMDriver.wsl
    elif has_lima and (has_vz or has_qemu):
        vm_driver = VMDriver.lima
    else:
        console.print(
            "[red]Error: Could not find a compatible VM runtime. Please follow the installation instructions at https://docs.beeai.dev/introduction/installation[/red]"
        )
        sys.exit(1)

    if vm_driver == VMDriver.lima and not (importlib.resources.files("beeai_cli") / "data" / "limactl").is_file():
        console.print(
            f"[yellow]Warning: Using external Lima from {shutil.which('limactl')}. This is fine in development, as long as the version matches.[/yellow]"
        )

    return vm_driver


async def _platform_status(vm_name: str) -> str | None:
    try:
        match _vm_driver():
            case VMDriver.lima:
                result = await run_command(
                    [_limactl_exe(), "--tty=false", "list", "--format=json"],
                    "Looking for existing BeeAI platform in Lima",
                    env={"LIMA_HOME": str(Configuration().lima_home)},
                    cwd="/",
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
            case VMDriver.wsl:
                running = (
                    (
                        await run_command(
                            ["wsl.exe", "--list", "--running", "--quiet"],
                            "Looking for running BeeAI platform in WSL",
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
                            "Looking for existing BeeAI platform in WSL",
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
    verbose: typing.Annotated[bool, typer.Option("-v", help="Show verbose output")] = False,
):
    """Start BeeAI platform."""
    with verbosity(verbose):
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

        if _vm_driver() == VMDriver.wsl:
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
            home = (
                pathlib.Path.home()
                if platform.system() == "Windows"
                else pathlib.Path(
                    (
                        await run_command(
                            ["/bin/sh", "-c", '''wslpath "$(cmd.exe /c 'echo %USERPROFILE%')"'''],
                            "Detecting home path",
                        )
                    )
                    .stdout.decode()
                    .strip()
                )
            )
            (home / ".wslconfig").touch()
            with (home / ".wslconfig").open("r+") as f:
                config = configparser.ConfigParser()
                f.seek(0)
                config.read_file(f)
                if not config.has_section("wsl2"):
                    config.add_section("wsl2")
                if config.get("wsl2", "networkingMode", fallback=None) != "mirrored":
                    config.set("wsl2", "networkingMode", "mirrored")
                    f.seek(0)
                    f.truncate(0)
                    config.write(f)
                    f.close()
                    if platform.system() == "Linux":
                        console.print(
                            "WSL networking mode has been updated. Please re-open WSL and run [green]beeai platform start[/green] again."
                        )
                        await run_command(["wsl.exe", "--shutdown"], "Shutting down WSL")
                        sys.exit(1)
                    else:
                        await run_command(["wsl.exe", "--shutdown"], "Updating WSL2 networking")

        # Start VM
        Configuration().home.mkdir(exist_ok=True)
        status = await _platform_status(vm_name)
        if not status:
            await run_command(
                {
                    VMDriver.lima: [_limactl_exe(), "--tty=false", "delete", "--force", vm_name],
                    VMDriver.wsl: ["wsl.exe", "--unregister", vm_name],
                }[_vm_driver()],
                "Cleaning up remains of previous instance",
                env={"LIMA_HOME": str(Configuration().lima_home)},
                check=False,
                cwd="/",
            )
            templates_dir = Configuration().lima_home / "_templates"
            if _vm_driver() == VMDriver.lima:
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
                            "mounts": [{"location": "/tmp/beeai", "mountPoint": "/tmp/beeai", "writable": True}],
                            "containerd": {"system": False, "user": False},
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
                            "memory": "8GiB",
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
                    VMDriver.wsl: [
                        "wsl.exe",
                        "--install",
                        "--name",
                        vm_name,
                        "--no-launch",
                        "--web-download",
                    ],
                }[_vm_driver()],
                "Creating a " + {VMDriver.lima: "Lima VM", VMDriver.wsl: "WSL distribution"}[_vm_driver()],
                env={
                    "LIMA_HOME": str(Configuration().lima_home),
                    # Hotfix for port-forwarding until this issue is resolved:
                    # https://github.com/lima-vm/lima/issues/3601#issuecomment-2936952923
                    "LIMA_SSH_PORT_FORWARDER": "true",
                },
                cwd="/",
            )
        elif status != "running":
            await run_command(
                {
                    VMDriver.lima: [_limactl_exe(), "--tty=false", "start", "--memory=8", vm_name],
                    VMDriver.wsl: ["wsl.exe", "--user", "root", "--distribution", vm_name, "dbus-launch", "true"],
                }[_vm_driver()],
                "Starting up",
                env={
                    "LIMA_HOME": str(Configuration().lima_home),
                    # Hotfix for port-forwarding until this issue is resolved:
                    # https://github.com/lima-vm/lima/issues/3601#issuecomment-2936952923
                    "LIMA_SSH_PORT_FORWARDER": "true",
                },
                cwd="/",
            )
        else:
            console.print("Updating an existing instance.")

        # Configure start-at-login for Lima
        if _vm_driver() == VMDriver.lima:
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
                cwd="/",
            )

        # Set up WSL
        if _vm_driver() == VMDriver.wsl:
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

            # Set-up host.docker.internal -> localhost
            await run_command(
                [
                    "wsl.exe",
                    "--user",
                    "root",
                    "--distribution",
                    vm_name,
                    "--",
                    "k3s",
                    "kubectl",
                    "--kubeconfig=/etc/rancher/k3s/k3s.yaml",
                    "apply",
                    "-f",
                    "-",
                ],
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
                                """\
                                host.docker.internal {
                                    hosts {
                                        127.0.0.1 host.docker.internal
                                        fallthrough
                                    }
                                }
                                """
                            )
                        },
                    }
                ).encode(),
            )

        # Import images
        for image in import_images:
            await import_image(image, vm_name=vm_name)

        # Deploy HelmChart
        await run_command(
            [
                *{
                    VMDriver.lima: [_limactl_exe(), "shell", vm_name, "--"],
                    VMDriver.wsl: ["wsl.exe", "--user", "root", "--distribution", vm_name, "--"],
                }[_vm_driver()],
                "k3s",
                "kubectl",
                "--kubeconfig=/etc/rancher/k3s/k3s.yaml",
                "apply",
                "--server-side",
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
                        "timeout": "1h0m0s",
                        "chartContent": base64.b64encode(
                            (importlib.resources.files("beeai_cli") / "data" / "helm-chart.tgz").read_bytes()
                        ).decode(),
                        "targetNamespace": "default",
                        "valuesContent": yaml.dump(
                            {
                                "hostNetwork": True,
                                "externalRegistries": {"public_github": str(Configuration().agent_registry)},
                                "encryptionKey": "Ovx8qImylfooq4-HNwOzKKDcXLZCB3c_m0JlB9eJBxc=",  # Dummy key for local use
                                "features": {"uiNavigation": True, "selfRegistration": True},
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
                    VMDriver.wsl: ["wsl.exe", "--user", "root", "--distribution", vm_name, "--"],
                }[_vm_driver()],
                "k3s",
                "kubectl",
                "--kubeconfig=/etc/rancher/k3s/k3s.yaml",
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
                    VMDriver.wsl: ["wsl.exe", "--user", "root", "--distribution", vm_name, "--"],
                }[_vm_driver()],
                "k3s",
                "kubectl",
                "--kubeconfig=/etc/rancher/k3s/k3s.yaml",
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
                    VMDriver.wsl: ["wsl.exe", "--user", "root", "--distribution", vm_name, "--"],
                }[_vm_driver()],
                "k3s",
                "kubectl",
                "--kubeconfig=/etc/rancher/k3s/k3s.yaml",
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
        status = await _platform_status(vm_name)
        if not status:
            console.print("BeeAI platform not found. Nothing to stop.")
            return
        await run_command(
            {
                VMDriver.lima: [_limactl_exe(), "--tty=false", "stop", "--force", vm_name],
                VMDriver.wsl: ["wsl.exe", "--terminate", vm_name],
            }[_vm_driver()],
            "Stopping BeeAI VM",
            env={"LIMA_HOME": str(Configuration().lima_home)},
            cwd="/",
        )
        console.print("[green]BeeAI platform stopped successfully.[/green]")


@app.command("delete")
async def delete(
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "beeai-platform",
    verbose: typing.Annotated[bool, typer.Option("-v", help="Show verbose output")] = False,
):
    """Delete BeeAI platform."""
    with verbosity(verbose):
        await run_command(
            {
                VMDriver.lima: [_limactl_exe(), "--tty=false", "delete", "--force", vm_name],
                VMDriver.wsl: ["wsl.exe", "--unregister", vm_name],
            }[_vm_driver()],
            "Deleting BeeAI platform",
            env={"LIMA_HOME": str(Configuration().lima_home)},
            check=False,
            cwd="/",
        )
        console.print("[green]BeeAI platform deleted successfully.[/green]")


@app.command("import")
async def import_image(
    tag: typing.Annotated[str, typer.Argument(help="Docker image tag to import")],
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "beeai-platform",
    verbose: typing.Annotated[bool, typer.Option("-v", help="Show verbose output")] = False,
):
    """Import a local docker image into the BeeAI platform."""
    with verbosity(verbose):
        if (await _platform_status(vm_name)) != "running":
            console.print("[red]BeeAI platform is not running.[/red]")
            sys.exit(1)

        if platform.system() == "Windows":
            image_directory = pathlib.Path(os.environ.get("TMP")) / "beeai"
        elif shutil.which("wsl.exe"):
            image_directory = (
                pathlib.Path(
                    (
                        await run_command(
                            ["/bin/sh", "-c", '''wslpath "$(cmd.exe /c 'echo %TMP%')"'''],
                            "Detecting temporary directory path",
                        )
                    )
                    .stdout.decode()
                    .strip()
                )
                / "beeai"
            )
        else:
            image_directory = pathlib.Path("/tmp/beeai")

        image_directory.mkdir(exist_ok=True, parents=True)
        image_filename = str(uuid.uuid4())
        image_path = image_directory / image_filename

        try:
            await run_command(
                ["docker", "image", "save", "-o", str(image_path), tag],
                f"Exporting image {tag} from Docker",
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
                if _vm_driver() == VMDriver.wsl
                else f"/tmp/beeai/{image_filename}"
            )

            await run_command(
                {
                    VMDriver.lima: [_limactl_exe(), "--tty=false", "shell", vm_name, "--"],
                    VMDriver.wsl: ["wsl.exe", "--user", "root", "--distribution", vm_name, "--"],
                }[_vm_driver()]
                + [
                    "/bin/sh",
                    "-c",
                    f"{'sudo' if _vm_driver() == VMDriver.lima else ''} k3s ctr images import {vm_image_path}",
                ],
                f"Importing image {tag} into BeeAI platform",
                env={"LIMA_HOME": str(Configuration().lima_home)},
                cwd="/",
            )
        finally:
            image_path.unlink()


@app.command("exec")
async def exec(
    command: typing.Annotated[list[str] | None, typer.Argument()] = None,
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "beeai-platform",
    verbose: typing.Annotated[bool, typer.Option("-v", help="Show verbose output")] = False,
):
    """For debugging -- execute a command inside the BeeAI platform VM."""
    with verbosity(verbose, show_success_status=False):
        command = command or ["/bin/sh"]
        if (await _platform_status(vm_name)) != "running":
            console.print("[red]BeeAI platform is not running.[/red]")
            sys.exit(1)
        await anyio.run_process(
            [
                *{
                    VMDriver.lima: [_limactl_exe(), "shell", f"--tty={sys.stdin.isatty()}", vm_name, "--"],
                    VMDriver.wsl: ["wsl.exe", "--user", "root", "--distribution", vm_name, "--"],
                }[_vm_driver()],
                *command,
            ],
            input=None if sys.stdin.isatty() else sys.stdin.read(),
            check=False,
            stdout=None,
            stderr=None,
            env={**os.environ, "LIMA_HOME": str(Configuration().lima_home)},
            cwd="/",
        )
