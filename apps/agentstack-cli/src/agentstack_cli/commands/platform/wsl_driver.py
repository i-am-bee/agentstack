# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import configparser
import os
import pathlib
import platform
import sys
import tempfile
import textwrap
import typing
import uuid

import anyio
import pydantic
import yaml

from agentstack_cli.commands.platform.base_driver import BaseDriver, ImagePullMode
from agentstack_cli.configuration import Configuration
from agentstack_cli.console import console
from agentstack_cli.utils import run_command


class WSLDriver(BaseDriver):
    @typing.override
    async def run_in_vm(
        self,
        command: list[str],
        message: str,
        env: dict[str, str] | None = None,
        input: bytes | None = None,
        check: bool = True,
    ):
        return await run_command(
            ["wsl.exe", "--user", "root", "--distribution", self.vm_name, "--", *command],
            message,
            env={**(env or {}), "WSL_UTF8": "1", "WSLENV": os.getenv("WSLENV", "") + ":WSL_UTF8"},
            input=input,
            check=check,
        )

    @typing.override
    async def status(self) -> typing.Literal["running"] | str | None:
        try:
            for status, cmd in [("running", ["--running"]), ("stopped", [])]:
                result = await run_command(
                    ["wsl.exe", "--list", "--quiet", *cmd],
                    f"Looking for {status} Agent Stack platform in WSL",
                    env={"WSL_UTF8": "1", "WSLENV": os.getenv("WSLENV", "") + ":WSL_UTF8"},
                )
                if self.vm_name in result.stdout.decode().splitlines():
                    return status
            return None
        except Exception:
            return None

    @typing.override
    async def create_vm(self):
        if (await run_command(["wsl.exe", "--status"], "Checking for WSL2", check=False)).returncode != 0:
            console.error(
                "WSL is not installed. Please follow the Agent Stack installation instructions: https://agentstack.beeai.dev/introduction/quickstart#windows"
            )
            console.hint(
                "Run [green]wsl.exe --install[/green] as administrator. If you just did this, restart your PC and run the same command again. Full installation may require up to two restarts. WSL is properly set up once you reach a working Linux terminal. You can verify this by running [green]wsl.exe[/green] without arguments."
            )
            sys.exit(1)

        config_file = (
            pathlib.Path.home()
            if platform.system() == "Windows"
            else pathlib.Path(
                (
                    await run_command(
                        ["/bin/sh", "-c", '''wslpath "$(cmd.exe /c 'echo %USERPROFILE%')"'''], "Detecting home path"
                    )
                )
                .stdout.decode()
                .strip()
            )
        ) / ".wslconfig"
        config_file.touch()
        with config_file.open("r+") as f:
            config = configparser.ConfigParser()
            f.seek(0)
            config.read_file(f)

            if not config.has_section("wsl2"):
                config.add_section("wsl2")

            wsl2_networking_mode = config.get("wsl2", "networkingMode", fallback=None)
            if wsl2_networking_mode and wsl2_networking_mode != "nat":
                config.set("wsl2", "networkingMode", "nat")
                f.seek(0)
                f.truncate(0)
                config.write(f)

                if platform.system() == "Linux":
                    console.warning(
                        "WSL networking mode updated. Please close WSL, run [green]wsl --shutdown[/green] from PowerShell, re-open WSL and run [green]agentstack platform start[/green] again."
                    )
                    sys.exit(1)
                await run_command(["wsl.exe", "--shutdown"], "Updating WSL2 networking")

        Configuration().home.mkdir(exist_ok=True)
        if not await self.status():
            await run_command(
                ["wsl.exe", "--unregister", self.vm_name], "Cleaning up remains of previous instance", check=False
            )
            await run_command(
                ["wsl.exe", "--unregister", "beeai-platform"], "Cleaning up remains of legacy instance", check=False
            )
            await run_command(
                ["wsl.exe", "--install", "--name", self.vm_name, "--no-launch", "--web-download"],
                "Creating a WSL distribution",
            )

        await self.run_in_vm(
            [
                "sh",
                "-c",
                "echo '[network]\ngenerateResolvConf = false\n[boot]\nsystemd=true\n' >/etc/wsl.conf && rm /etc/resolv.conf && echo 'nameserver 1.1.1.1\n' >/etc/resolv.conf && chattr +i /etc/resolv.conf",
            ],
            "Setting up DNS configuration",
            check=False,
        )

        await run_command(["wsl.exe", "--terminate", self.vm_name], "Restarting Agent Stack VM")
        await self.run_in_vm(["dbus-launch", "true"], "Ensuring persistence of Agent Stack VM")

    @typing.override
    async def deploy(
        self,
        set_values_list: list[str],
        values_file: pathlib.Path | None = None,
        image_pull_mode: ImagePullMode = ImagePullMode.guest,
    ) -> None:
        host_ip = (
            (
                await self.run_in_vm(
                    ["bash", "-c", "ip route show | grep -i default | cut -d' ' -f3"],
                    "Detecting host IP address",
                )
            )
            .stdout.decode()
            .strip()
        )
        await self.run_in_vm(
            ["k3s", "kubectl", "apply", "-f", "-"],
            "Setting up internal networking",
            input=yaml.dump(
                {
                    "apiVersion": "v1",
                    "kind": "ConfigMap",
                    "metadata": {"name": "coredns-custom", "namespace": "kube-system"},
                    "data": {
                        "default.server": f"host.docker.internal {{\n    hosts {{\n        {host_ip} host.docker.internal\n        fallthrough\n    }}\n}}"
                    },
                }
            ).encode(),
        )
        await super().deploy(set_values_list=set_values_list, values_file=values_file, image_pull_mode=image_pull_mode)
        await self.run_in_vm(
            ["sh", "-c", "cat >/etc/systemd/system/kubectl-port-forward@.service"],
            "Installing systemd unit for port-forwarding",
            input=textwrap.dedent("""\
            [Unit]
            Description=Kubectl Port Forward for service %%i
            After=network.target

            [Service]
            Type=simple
            ExecStart=/bin/bash -c 'IFS=":" read svc port <<< "%i"; exec /usr/local/bin/kubectl port-forward --address=127.0.0.1 svc/$svc $port:$port'
            Restart=on-failure
            User=root

            [Install]
            WantedBy=multi-user.target
            """).encode(),
        )
        await self.run_in_vm(["systemctl", "daemon-reexec"], "Reloading systemd")
        services_json = (
            await self.run_in_vm(
                ["k3s", "kubectl", "get", "svc", "--field-selector=spec.type=LoadBalancer", "--output=json"],
                "Detecting ports to forward",
            )
        ).stdout
        ServicePort = typing.TypedDict("ServicePort", {"port": int, "name": str})
        ServiceSpec = typing.TypedDict("ServiceSpec", {"ports": list[ServicePort]})
        ServiceMetadata = typing.TypedDict("ServiceMetadata", {"name": str, "namespace": str})
        Service = typing.TypedDict("Service", {"metadata": ServiceMetadata, "spec": ServiceSpec})
        Services = typing.TypedDict("Services", {"items": list[Service]})
        for service in pydantic.TypeAdapter(Services).validate_json(services_json)["items"]:
            name = service["metadata"]["name"]
            for port_item in service["spec"]["ports"]:
                port = port_item["port"]
                await self.run_in_vm(
                    ["systemctl", "enable", "--now", f"kubectl-port-forward@{name}:{port}.service"],
                    f"Starting port-forward for {name}:{port}",
                )

    @typing.override
    async def stop(self):
        await run_command(["wsl.exe", "--terminate", self.vm_name], "Stopping Agent Stack VM")

    @typing.override
    async def delete(self):
        await run_command(["wsl.exe", "--unregister", self.vm_name], "Deleting Agent Stack platform", check=False)

    @typing.override
    async def import_images(self, *tags: str) -> None:
        if not tags:
            return

        # Create a temporary file on Windows
        with tempfile.NamedTemporaryFile(suffix=".tar", delete=False) as tmp_file:
            windows_path = pathlib.Path(tmp_file.name)
            tmp_file.close()

        try:
            # Export images from Docker on Windows host
            await run_command(
                ["docker", "image", "save", "-o", str(windows_path), *tags],
                f"Exporting image{'' if len(tags) == 1 else 's'} {', '.join(tags)} from Docker",
            )

            # Convert Windows path to WSL path
            # Example: C:\Users\...\temp.tar -> /mnt/c/Users/.../temp.tar
            wsl_path = self._windows_path_to_wsl(windows_path)

            # Import images into k3s inside WSL2
            await self.run_in_vm(
                ["/bin/sh", "-c", f"k3s ctr images import {wsl_path}"],
                f"Importing image{'' if len(tags) == 1 else 's'} {', '.join(tags)} into Agent Stack platform",
            )
        finally:
            # Clean up the temporary file
            windows_path.unlink(missing_ok=True)

    def _windows_path_to_wsl(self, windows_path: pathlib.Path) -> str:
        """Convert a Windows path to WSL path format.

        Example: C:\\Users\\name\\temp.tar -> /mnt/c/Users/name/temp.tar
        """
        # Get the absolute path
        abs_path = windows_path.resolve()
        path_str = str(abs_path)

        # Handle drive letter (e.g., C:\ -> /mnt/c/)
        if len(path_str) >= 2 and path_str[1] == ":":
            drive = path_str[0].lower()
            rest_of_path = path_str[2:].replace("\\", "/")
            # Remove leading slash if present
            if rest_of_path.startswith("/"):
                rest_of_path = rest_of_path[1:]
            return f"/mnt/{drive}/{rest_of_path}"

        # If no drive letter, just convert backslashes to forward slashes
        return path_str.replace("\\", "/")

    @typing.override
    async def import_image_to_internal_registry(self, tag: str) -> None:
        # 1. Check if registry is running
        try:
            await self.run_in_vm(
                ["k3s", "kubectl", "get", "svc", "agentstack-registry-svc"],
                "Checking internal registry availability",
            )
        except Exception as e:
            console.warning(f"Internal registry service not found. Push might fail: {e}")

        # 2. Export image from Docker on Windows host to temporary file
        with tempfile.NamedTemporaryFile(suffix=".tar", delete=False) as tmp_file:
            windows_path = pathlib.Path(tmp_file.name)
            tmp_file.close()

        try:
            await run_command(
                ["docker", "image", "save", "-o", str(windows_path), tag],
                f"Exporting image {tag} from Docker",
            )

            # Convert Windows path to WSL path
            wsl_path = self._windows_path_to_wsl(windows_path)
            image_filename = windows_path.name
            # Get parent directory using POSIX path to preserve forward slashes
            wsl_parent_dir = str(pathlib.PurePosixPath(wsl_path).parent)

            # 3 & 4. Run Crane Job to push to internal registry
            crane_image = "ghcr.io/i-am-bee/alpine/crane:0.20.6"
            for image in self.loaded_images:
                if "alpine/crane" in image:
                    crane_image = image
                    break

            job_name = f"push-{uuid.uuid4().hex[:6]}"
            job_def = {
                "apiVersion": "batch/v1",
                "kind": "Job",
                "metadata": {"name": job_name, "namespace": "default"},
                "spec": {
                    "backoffLimit": 0,
                    "ttlSecondsAfterFinished": 60,
                    "template": {
                        "spec": {
                            "restartPolicy": "Never",
                            "containers": [
                                {
                                    "name": "crane",
                                    "image": crane_image,
                                    "command": ["crane", "push", f"/workspace/{image_filename}", tag, "--insecure"],
                                    "volumeMounts": [{"name": "workspace", "mountPath": "/workspace"}],
                                }
                            ],
                            "volumes": [
                                {
                                    "name": "workspace",
                                    "hostPath": {"path": wsl_parent_dir},
                                }
                            ],
                        }
                    },
                },
            }

            await self.run_in_vm(
                ["k3s", "kubectl", "apply", "-f", "-"], "Starting push job", input=yaml.dump(job_def).encode()
            )
            await self.run_in_vm(
                ["k3s", "kubectl", "wait", "--for=condition=complete", f"job/{job_name}", "--timeout=300s"],
                "Waiting for push to complete",
            )
            await self.run_in_vm(["k3s", "kubectl", "delete", "job", job_name], "Cleaning up push job")
        finally:
            # Clean up the temporary file
            windows_path.unlink(missing_ok=True)

    @typing.override
    async def exec(self, command: list[str]):
        await anyio.run_process(
            ["wsl.exe", "--user", "root", "--distribution", self.vm_name, "--", *command],
            input=None if sys.stdin.isatty() else sys.stdin.read().encode(),
            check=False,
            stdout=None,
            stderr=None,
        )
