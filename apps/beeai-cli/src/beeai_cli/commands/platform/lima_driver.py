# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import importlib.resources
import os
import shutil
import sys
import tempfile
import typing
import uuid
from subprocess import CompletedProcess

import anyio
import psutil
import pydantic
import yaml

from beeai_cli.commands.platform.base_driver import BaseDriver
from beeai_cli.configuration import Configuration
from beeai_cli.console import console
from beeai_cli.utils import run_command


class LimaDriver(BaseDriver):
    limactl_exe: str

    def __init__(self, vm_name: str = "beeai-platform"):
        super().__init__(vm_name)
        bundled_limactl_exe = importlib.resources.files("beeai_cli") / "data" / "limactl"
        if bundled_limactl_exe.is_file():
            self.limactl_exe = str(bundled_limactl_exe)
        else:
            self.limactl_exe = str(shutil.which("limactl"))
            console.warning(f"Using external Lima from {self.limactl_exe}")

    @typing.override
    async def run_in_vm(
        self,
        command: list[str],
        message: str,
        env: dict[str, str] | None = None,
        input: bytes | None = None,
    ) -> CompletedProcess[bytes]:
        return await run_command(
            [self.limactl_exe, "shell", f"--tty={sys.stdin.isatty()}", self.vm_name, "--", "sudo", *command],
            message,
            env={"LIMA_HOME": str(Configuration().lima_home)} | (env or {}),
            cwd="/",
            input=input,
        )

    @typing.override
    async def status(self) -> typing.Literal["running"] | str | None:
        try:
            result = await run_command(
                [self.limactl_exe, "--tty=false", "list", "--format=json"],
                "Looking for existing BeeAI platform in Lima",
                env={"LIMA_HOME": str(Configuration().lima_home)},
                cwd="/",
            )

            for line in result.stdout.decode().split("\n"):
                if not line:
                    continue
                status = pydantic.TypeAdapter(typing.TypedDict("Status", {"name": str, "status": str})).validate_json(
                    line
                )
                if status["name"] == self.vm_name:
                    return status["status"].lower()
            return None
        except Exception:
            return None

    @typing.override
    async def create_vm(self):
        Configuration().home.mkdir(exist_ok=True)
        current_status = await self.status()

        if not current_status:
            await run_command(
                [self.limactl_exe, "--tty=false", "delete", "--force", self.vm_name],
                "Cleaning up remains of previous instance",
                env={"LIMA_HOME": str(Configuration().lima_home)},
                check=False,
                cwd="/",
            )

            total_memory_gib = typing.cast(int, psutil.virtual_memory().total / (1024**3))

            if total_memory_gib < 4:
                console.error("Not enough memory. BeeAI platform requires at least 4 GB of RAM.")
                sys.exit(1)

            if total_memory_gib < 8:
                console.warning("Less than 8 GB of RAM detected. Performance may be degraded.")

            vm_memory_gib = round(min(8, max(3, total_memory_gib / 2)))

            with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete_on_close=False) as template_file:
                template_file.write(
                    yaml.dump(
                        {
                            "images": [
                                {
                                    "location": "https://cloud-images.ubuntu.com/releases/noble/release/ubuntu-24.04-server-cloudimg-amd64.img",
                                    "arch": "x86_64",
                                },
                                {
                                    "location": "https://cloud-images.ubuntu.com/releases/noble/release/ubuntu-24.04-server-cloudimg-arm64.img",
                                    "arch": "aarch64",
                                },
                            ],
                            "portForwards": [
                                {
                                    "guestIP": "127.0.0.1",
                                    "guestPortRange": [1024, 65535],
                                    "hostPortRange": [1024, 65535],
                                    "hostIP": "127.0.0.1",
                                },
                                {"guestIP": "0.0.0.0", "proto": "any", "ignore": True},
                            ],
                            "mounts": [{"location": "/tmp/beeai", "mountPoint": "/tmp/beeai", "writable": True}],
                            "containerd": {"system": False, "user": False},
                            "hostResolver": {"hosts": {"host.docker.internal": "host.lima.internal"}},
                            "memory": f"{vm_memory_gib}GiB",
                        }
                    )
                )
                template_file.flush()
                template_file.close()
                await run_command(
                    [
                        self.limactl_exe,
                        "--tty=false",
                        "start",
                        str(template_file.name),
                        f"--name={self.vm_name}",
                    ],
                    "Creating a Lima VM",
                    env={"LIMA_HOME": str(Configuration().lima_home)},
                    cwd="/",
                )
        elif current_status != "running":
            await run_command(
                [self.limactl_exe, "--tty=false", "start", self.vm_name],
                "Starting up",
                env={"LIMA_HOME": str(Configuration().lima_home)},
                cwd="/",
            )
        else:
            console.info("Updating an existing instance.")

    @typing.override
    async def stop(self):
        await run_command(
            [self.limactl_exe, "--tty=false", "stop", "--force", self.vm_name],
            "Stopping BeeAI VM",
            env={"LIMA_HOME": str(Configuration().lima_home)},
            cwd="/",
        )

    @typing.override
    async def delete(self):
        await run_command(
            [self.limactl_exe, "--tty=false", "delete", "--force", self.vm_name],
            "Deleting BeeAI platform",
            env={"LIMA_HOME": str(Configuration().lima_home)},
            check=False,
            cwd="/",
        )

    @typing.override
    async def import_image(self, tag: str):
        image_dir = anyio.Path("/tmp/beeai")
        await image_dir.mkdir(exist_ok=True, parents=True)
        image_file = str(uuid.uuid4())
        image_path = image_dir / image_file

        try:
            await run_command(
                ["docker", "image", "save", "-o", str(image_path), tag], f"Exporting image {tag} from Docker"
            )
            await self.run_in_vm(
                ["/bin/sh", "-c", f"k3s ctr images import /tmp/beeai/{image_file}"],
                f"Importing image {tag} into BeeAI platform",
            )
        finally:
            await image_path.unlink(missing_ok=True)

    @typing.override
    async def exec(self, command: list[str]):
        await anyio.run_process(
            [self.limactl_exe, "shell", f"--tty={sys.stdin.isatty()}", self.vm_name, "--", *command],
            input=None if sys.stdin.isatty() else sys.stdin.read().encode(),
            check=False,
            stdout=None,
            stderr=None,
            env={**os.environ, "LIMA_HOME": str(Configuration().lima_home)},
            cwd="/",
        )
