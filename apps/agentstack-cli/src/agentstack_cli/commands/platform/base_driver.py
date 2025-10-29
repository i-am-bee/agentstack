# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import abc
import importlib.resources
import pathlib
import shlex
import typing
from subprocess import CompletedProcess
from textwrap import dedent

import anyio
import pydantic
import yaml
from tenacity import AsyncRetrying, stop_after_attempt

import agentstack_cli.commands.platform.istio
from agentstack_cli.configuration import Configuration


class BaseDriver(abc.ABC):
    vm_name: str

    def __init__(self, vm_name: str = "agentstack-platform"):
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
    async def status(self) -> typing.Literal["running"] | str | None: ...

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
        # Configure k3s registry for local registry access
        registry_config = dedent(
            """\
            mirrors:
              "agentstack-platform-registry-svc.default:5001":
                endpoint:
                  - "http://localhost:30501"
            configs:
              "agentstack-platform-registry-svc.default:5001":
                tls:
                  insecure_skip_verify: true
            """
        )

        await self.run_in_vm(
            [
                "sh",
                "-c",
                (
                    f"sudo mkdir -p /etc/rancher/k3s /registry-data && "
                    f"echo '{registry_config}' | "
                    "sudo tee /etc/rancher/k3s/registries.yaml > /dev/null"
                ),
            ],
            "Configuring k3s registry",
        )

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

    async def deploy(
        self,
        set_values_list: list[str],
        values_file: pathlib.Path | None = None,
        import_images: list[str] | None = None,
    ) -> None:
        await self.run_in_vm(
            ["sh", "-c", "mkdir -p /tmp/agentstack && cat >/tmp/agentstack/chart.tgz"],
            "Preparing Helm chart",
            input=(importlib.resources.files("agentstack_cli") / "data" / "helm-chart.tgz").read_bytes(),
        )
        values = {
            **{svc: {"service": {"type": "LoadBalancer"}} for svc in ["collector", "docling", "ui", "phoenix"]},
            "hostNetwork": True,
            "externalRegistries": {"public_github": str(Configuration().agent_registry)},
            "encryptionKey": "Ovx8qImylfooq4-HNwOzKKDcXLZCB3c_m0JlB9eJBxc=",
            "features": {
                "uiNavigation": True,
                "selfRegistration": True,
                "localSetup": True,
                "generateConversationTitle": False,  # TODO: enable when UI implementation is ready
            },
            "auth": {"enabled": False},
        }
        if values_file:
            values.update(yaml.safe_load(values_file.read_text()))
        await self.run_in_vm(
            ["sh", "-c", "cat >/tmp/agentstack/values.yaml"],
            "Preparing Helm values",
            input=yaml.dump(values).encode("utf-8"),
        )

        images_str = (
            await self.run_in_vm(
                [
                    "/bin/bash",
                    "-c",
                    "helm template agentstack /tmp/agentstack/chart.tgz --values=/tmp/agentstack/values.yaml "
                    + " ".join(shlex.quote(f"--set={value}") for value in set_values_list)
                    + " | sed -n '/^\\s*image:/{ /{{/!{ s/.*image:\\s*//p } }'",
                ],
                "Listing necessary images",
            )
        ).stdout.decode()
        for image in import_images or []:
            await self.import_image(image)
        for image in {typing.cast(str, yaml.safe_load(line)) for line in images_str.splitlines()} - set(
            import_images or []
        ):
            async for attempt in AsyncRetrying(stop=stop_after_attempt(5)):
                with attempt:
                    attempt_num = attempt.retry_state.attempt_number
                    await self.run_in_vm(
                        [
                            "k3s",
                            "ctr",
                            "image",
                            "pull",
                            image if "." in image.split("/")[0] else f"docker.io/{image}",
                        ],
                        f"Pulling image {image}" + (f" (attempt {attempt_num})" if attempt_num > 1 else ""),
                    )

        if any("auth.oidc.enabled=true" in value.lower() for value in set_values_list):
            await agentstack_cli.commands.platform.istio.install(driver=self)

        kubeconfig_path = anyio.Path(Configuration().lima_home) / self.vm_name / "copied-from-guest" / "kubeconfig.yaml"
        await kubeconfig_path.parent.mkdir(parents=True, exist_ok=True)
        await kubeconfig_path.write_text(
            (
                await self.run_in_vm(
                    ["/bin/cat", "/etc/rancher/k3s/k3s.yaml"],
                    "Copying kubeconfig from Agent Stack platform",
                )
            ).stdout.decode()
        )

        await self.run_in_vm(
            [
                "helm",
                "upgrade",
                "--install",
                "agentstack",
                "/tmp/agentstack/chart.tgz",
                "--namespace=default",
                "--create-namespace",
                "--values=/tmp/agentstack/values.yaml",
                "--timeout=5m",
                "--wait",
                "--kubeconfig=/etc/rancher/k3s/k3s.yaml",
                *(f"--set={value}" for value in set_values_list),
            ],
            "Deploying Agent Stack platform with Helm",
        )

        if import_images:
            await self.run_in_vm(
                ["k3s", "kubectl", "rollout", "restart", "deployment"],
                "Restarting deployments to load imported images",
            )

    async def version(self) -> str | None:
        if (await self.status()) != "running":
            return None
        HelmStatus = typing.TypedDict("HelmStatus", {"status": str, "app_version": str})
        helm_status = pydantic.TypeAdapter(list[HelmStatus]).validate_json(
            (
                await self.run_in_vm(
                    [
                        "/usr/local/bin/helm",
                        "--kubeconfig=/etc/rancher/k3s/k3s.yaml",
                        "ls",
                        "--namespace=default",
                        "--filter=^agentstack$",
                        "-o",
                        "json",
                    ],
                    "Getting Agent Stack platform version",
                )
            ).stdout
        )
        if helm_status[0]["status"] != "deployed":
            return None
        return helm_status[0]["app_version"]
