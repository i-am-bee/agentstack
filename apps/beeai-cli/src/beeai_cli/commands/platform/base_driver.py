# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import abc
import importlib.resources
import typing
from subprocess import CompletedProcess

import anyio
import yaml

from beeai_cli.configuration import Configuration


class BaseDriver(abc.ABC):
    vm_name: str

    def __init__(self, vm_name: str = "beeai-platform"):
        self.vm_name = vm_name

    @abc.abstractmethod
    async def run_in_vm(
        self,
        command: list[str],
        message: str,
        env: dict[str, str] | None = None,
        input: bytes | None = None,
    ) -> CompletedProcess[bytes]: ...

    @abc.abstractmethod
    async def status(self) -> str | None: ...

    @abc.abstractmethod
    async def create_vm(self) -> None: ...

    @abc.abstractmethod
    async def stop(self) -> None: ...

    @abc.abstractmethod
    async def delete(self) -> None: ...

    @abc.abstractmethod
    async def import_image(self, tag: str) -> None: ...

    @abc.abstractmethod
    async def exec(self, command: list[str]) -> None: ...

    async def install_tools(self) -> None:
        await self.run_in_vm(
            [
                "sh",
                "-c",
                "which k3s || curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644 --https-listen-port=16443",
            ],
            "Installing k3s",
        )
        await self.run_in_vm(
            [
                "sh",
                "-c",
                "which helm || curl -sfL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash",
            ],
            "Installing Helm",
        )

    async def deploy(self, set_values_list: list[str], import_images: list[str] | None = None) -> None:
        await self.run_in_vm(
            ["sh", "-c", "mkdir -p /tmp/beeai && cat >/tmp/beeai/chart.tgz"],
            "Preparing Helm chart",
            input=(importlib.resources.files("beeai_cli") / "data" / "helm-chart.tgz").read_bytes(),
        )
        await self.run_in_vm(
            ["sh", "-c", "cat >/tmp/beeai/values.yaml"],
            "Preparing Helm values",
            input=yaml.dump(
                {
                    **{svc: {"service": {"type": "LoadBalancer"}} for svc in ["collector", "docling", "ui", "phoenix"]},
                    "hostNetwork": True,
                    "externalRegistries": {"public_github": str(Configuration().agent_registry)},
                    "encryptionKey": "Ovx8qImylfooq4-HNwOzKKDcXLZCB3c_m0JlB9eJBxc=",
                    "features": {"uiNavigation": True, "selfRegistration": True},
                    "auth": {"enabled": False},
                }
            ).encode("utf-8"),
        )

        rendered_yaml = (
            await self.run_in_vm(
                [
                    "helm",
                    "template",
                    "beeai",
                    "/tmp/beeai/chart.tgz",
                    "--values=/tmp/beeai/values.yaml",
                    *(f"--set={value}" for value in set_values_list),
                ],
                "Rendering Helm chart",
            )
        ).stdout.decode()
        for image in import_images or []:
            await self.import_image(image)
        for image in {
            typing.cast(str, yaml.safe_load(line.strip().removeprefix("image:").strip()))
            for line in rendered_yaml.splitlines()
            if line.strip().startswith("image:") and "{{" not in line
        } - set(import_images or []):
            await self.run_in_vm(
                [
                    "k3s",
                    "ctr",
                    "image",
                    "pull",
                    image if "." in image.split("/")[0] else f"docker.io/{image}",
                ],
                f"Pulling image {image}",
            )

        await self.run_in_vm(
            [
                "helm",
                "upgrade",
                "--install",
                "beeai",
                "/tmp/beeai/chart.tgz",
                "--namespace=default",
                "--create-namespace",
                "--values=/tmp/beeai/values.yaml",
                "--timeout=1h0m0s",
                "--wait",
                "--kubeconfig=/etc/rancher/k3s/k3s.yaml",
                *(f"--set={value}" for value in set_values_list),
            ],
            "Deploying BeeAI platform with Helm",
        )

        if import_images:
            await self.run_in_vm(
                ["k3s", "kubectl", "rollout", "restart", "deployment"],
                "Restarting deployments to load imported images",
            )

        kubeconfig_path = anyio.Path(Configuration().lima_home) / self.vm_name / "copied-from-guest" / "kubeconfig.yaml"
        await kubeconfig_path.parent.mkdir(parents=True, exist_ok=True)
        await kubeconfig_path.write_text(
            (
                await self.run_in_vm(
                    ["/bin/cat", "/etc/rancher/k3s/k3s.yaml"],
                    "Copying kubeconfig from BeeAI platform",
                )
            ).stdout.decode()
        )
