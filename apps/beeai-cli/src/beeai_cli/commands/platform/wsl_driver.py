# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import configparser
import os
import pathlib
import platform
import sys
import textwrap
import typing

import anyio
import pydantic
import yaml
from InquirerPy import inquirer
from InquirerPy.base.control import Choice

from beeai_cli.commands.platform.base_driver import BaseDriver
from beeai_cli.configuration import Configuration
from beeai_cli.console import console
from beeai_cli.utils import run_command


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
                    f"Looking for {status} BeeAI platform in WSL",
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
            await run_command(["wsl.exe", "--install", "--no-launch", "--web-download"], "Installing WSL2")
        await run_command(["wsl.exe", "--upgrade"], "Upgrading WSL2", check=False)

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

            if (
                config.get("wsl2", "networkingMode", fallback=None) != "mirrored"
                and await inquirer.select(  # type: ignore
                    textwrap.dedent("""\
                    The BeeAI platform needs to switch WSL to `mirrored` networking mode in order to support connecting to Windows applications -- like Ollama or self-registered agents. If you skip this step, these features won't be available.

                    However, the default `nat` mode is required by some software, like Docker Desktop or Rancher Desktop, to function properly. If you use such software, you may want to keep the default `nat` mode.

                    (It can be changed anytime later in C:/Users/<your name>/.wslconfig, followed by `wsl --shutdown` and `beeai platform start` to apply changes.)
                    """),
                    choices=[
                        Choice(
                            value=True,
                            name="Change WSL2 networking mode to `mirrored`",
                        ),
                        Choice(
                            value=False,
                            name="Leave WSL2 networking mode as `nat`",
                        ),
                    ],
                ).execute_async()
            ):
                config.set("wsl2", "networkingMode", "mirrored")
                f.seek(0)
                f.truncate(0)
                config.write(f)

                if platform.system() == "Linux":
                    console.warning(
                        "WSL networking mode updated. Please close WSL, run [green]wsl --shutdown[/green] from PowerShell, re-open WSL and run [green]beeai platform start[/green] again."
                    )
                    sys.exit(1)
                await run_command(["wsl.exe", "--shutdown"], "Updating WSL2 networking")

        Configuration().home.mkdir(exist_ok=True)
        if not await self.status():
            await run_command(
                ["wsl.exe", "--unregister", self.vm_name], "Cleaning up remains of previous instance", check=False
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

        await run_command(["wsl.exe", "--terminate", self.vm_name], "Restarting BeeAI VM")
        await self.run_in_vm(["dbus-launch", "true"], "Ensuring persistence of BeeAI VM")

    @typing.override
    async def deploy(
        self,
        set_values_list: list[str],
        values_file: pathlib.Path | None = None,
        import_images: list[str] | None = None,
    ) -> None:
        await self.run_in_vm(
            ["k3s", "kubectl", "apply", "-f", "-"],
            "Setting up internal networking",
            input=yaml.dump(
                {
                    "apiVersion": "v1",
                    "kind": "ConfigMap",
                    "metadata": {"name": "coredns-custom", "namespace": "kube-system"},
                    "data": {
                        "default.server": "host.docker.internal {\n    hosts {\n        127.0.0.1 host.docker.internal\n        fallthrough\n    }\n}"
                    },
                }
            ).encode(),
        )
        await super().deploy(set_values_list=set_values_list, values_file=values_file, import_images=import_images)
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
        await run_command(["wsl.exe", "--terminate", self.vm_name], "Stopping BeeAI VM")

    @typing.override
    async def delete(self):
        await run_command(["wsl.exe", "--unregister", self.vm_name], "Deleting BeeAI platform", check=False)

    @typing.override
    async def import_image(self, tag: str) -> None:
        raise NotImplementedError("Importing images is not supported on this platform.")

    @typing.override
    async def exec(self, command: list[str]):
        await anyio.run_process(
            ["wsl.exe", "--user", "root", "--distribution", self.vm_name, "--", *command],
            input=None if sys.stdin.isatty() else sys.stdin.read().encode(),
            check=False,
            stdout=None,
            stderr=None,
        )
