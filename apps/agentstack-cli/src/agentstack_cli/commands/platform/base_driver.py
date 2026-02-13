# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import abc
import importlib.resources
import json
import pathlib
import shlex
import typing
import uuid
from enum import StrEnum
from subprocess import CompletedProcess
from textwrap import dedent

import anyio
import yaml
from tenacity import AsyncRetrying, stop_after_attempt

from agentstack_cli.configuration import Configuration
from agentstack_cli.utils import merge, run_command


class ImagePullMode(StrEnum):
    guest = "guest"
    host = "host"
    hybrid = "hybrid"
    skip = "skip"


class BaseDriver(abc.ABC):
    vm_name: str

    def __init__(self, vm_name: str = "agentstack"):
        self.vm_name = vm_name
        self.loaded_images: set[str] = set()

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
    async def exec(self, command: list[str]) -> None: ...

    @abc.abstractmethod
    def _get_export_import_paths(self) -> tuple[str, str]: ...

    async def import_images(self, *tags: str) -> None:
        if not tags:
            return

        host_path, guest_path = self._get_export_import_paths()

        try:
            await run_command(
                ["docker", "image", "save", "-o", host_path, *tags],
                f"Exporting image{'' if len(tags) == 1 else 's'} {', '.join(tags)} from Docker",
            )
            await self.run_in_vm(
                ["/bin/sh", "-c", f"k3s ctr images import {guest_path}"],
                f"Importing image{'' if len(tags) == 1 else 's'} {', '.join(tags)} into Agent Stack platform",
            )
        finally:
            await anyio.Path(host_path).unlink(missing_ok=True)

    async def import_image_to_internal_registry(self, tag: str) -> None:
        host_path, guest_path = self._get_export_import_paths()

        try:
            await run_command(
                ["docker", "image", "save", "-o", str(host_path), tag],
                f"Exporting image {tag} from Docker",
            )
            job_name = f"push-{uuid.uuid4().hex[:6]}"
            await self.run_in_vm(
                ["k3s", "kubectl", "apply", "-f", "-"],
                "Starting push job",
                input=yaml.dump(
                    {
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
                                            "image": next(
                                                (image for image in self.loaded_images if "alpine/crane" in image),
                                                "ghcr.io/i-am-bee/alpine/crane:0.20.6",
                                            ),
                                            "command": [
                                                "crane",
                                                "push",
                                                f"/workspace/{pathlib.Path(host_path).name}",
                                                tag,
                                                "--insecure",
                                            ],
                                            "volumeMounts": [{"name": "workspace", "mountPath": "/workspace"}],
                                        }
                                    ],
                                    "volumes": [
                                        {
                                            "name": "workspace",
                                            "hostPath": {"path": str(pathlib.PurePosixPath(guest_path).parent)},
                                        }
                                    ],
                                }
                            },
                        },
                    }
                ).encode(),
            )
            await self.run_in_vm(
                ["k3s", "kubectl", "wait", "--for=condition=complete", f"job/{job_name}", "--timeout=300s"],
                "Waiting for push to complete",
            )
        finally:
            await anyio.Path(host_path).unlink(missing_ok=True)

    def _canonify(self, tag: str) -> str:
        return tag if "." in tag.split("/")[0] else f"docker.io/{tag}"

    async def _grab_image_shas(
        self,
        *,
        mode: typing.Literal["guest", "host"],
    ) -> dict[str, str]:
        return {
            tag: sha
            for line in (
                await run_command(
                    ["docker", "images", "--digests"],
                    "Listing host images",
                )
                if mode == "host"
                else await self.run_in_vm(
                    ["k3s", "ctr", "image", "ls"],
                    "Listing guest images",
                )
            )
            .stdout.decode()
            .splitlines()[1:]
            if (x := line.split())
            and (sha := x[2])
            and ((tag := self._canonify((x[0] + ":" + x[1]) if mode == "host" else x[0])) in self.loaded_images)
        }

    async def install_tools(self) -> None:
        registry_config = dedent(
            """\
            mirrors:
              "agentstack-registry-svc.default:5001":
                endpoint:
                  - "http://localhost:30501"
            configs:
              "agentstack-registry-svc.default:5001":
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
            "Configuring Kubernetes registry",
        )

        await self.run_in_vm(
            [
                "sh",
                "-c",
                "which k3s || curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644 --https-listen-port=16443",
            ],
            "Installing Kubernetes",
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
        image_pull_mode: ImagePullMode = ImagePullMode.guest,
    ) -> None:
        _ = await self.run_in_vm(
            ["sh", "-c", "mkdir -p /tmp/agentstack && cat >/tmp/agentstack/chart.tgz"],
            "Preparing Helm chart",
            input=(importlib.resources.files("agentstack_cli") / "data" / "helm-chart.tgz").read_bytes(),
        )
        values = {
            **{svc: {"service": {"type": "LoadBalancer"}} for svc in ["collector", "docling", "ui", "phoenix"]},
            "service": {"type": "LoadBalancer"},
            "externalRegistries": {"public_github": str(Configuration().agent_registry)},
            "encryptionKey": "Ovx8qImylfooq4-HNwOzKKDcXLZCB3c_m0JlB9eJBxc=",
            "trustProxyHeaders": True,
            "keycloak": {
                "uiClientSecret": "agentstack-ui-secret",
                "serverClientSecret": "agentstack-server-secret",
                "service": {"type": "LoadBalancer"},
                "auth": {"adminPassword": "admin"},
            },
            "features": {"uiLocalSetup": True},
            "providerBuilds": {"enabled": True},
            "localDockerRegistry": {"enabled": True},
            "auth": {"enabled": False},
        }
        if values_file:
            values = merge(values, yaml.safe_load(values_file.read_text()))
        await self.run_in_vm(
            ["sh", "-c", "cat >/tmp/agentstack/values.yaml"],
            "Preparing Helm values",
            input=yaml.dump(values).encode("utf-8"),
        )

        self.loaded_images = {
            self._canonify(typing.cast(str, yaml.safe_load(line)))
            for line in (
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
            )
            .stdout.decode()
            .splitlines()
        }

        images_to_import_from_host = set[str]()
        shas_guest_before = dict[str, str]()

        if image_pull_mode in {ImagePullMode.host, ImagePullMode.hybrid}:
            shas_guest_before = await self._grab_image_shas(mode="guest")
            shas_host = await self._grab_image_shas(mode="host")
            if image_pull_mode == ImagePullMode.host and (images_to_pull := self.loaded_images - shas_host.keys()):
                for image in images_to_pull:
                    await run_command(
                        ["docker", "pull", image],
                        f"Pulling image {image} on host",
                    )
                shas_host = await self._grab_image_shas(mode="host")
            images_to_import_from_host = dict(shas_host.items() - shas_guest_before.items()).keys() & self.loaded_images
            await self.import_images(*images_to_import_from_host)

        if image_pull_mode in {ImagePullMode.guest, ImagePullMode.hybrid}:
            for image in self.loaded_images - images_to_import_from_host:
                async for attempt in AsyncRetrying(stop=stop_after_attempt(5)):
                    with attempt:
                        attempt_num = attempt.retry_state.attempt_number
                        await self.run_in_vm(
                            ["k3s", "ctr", "image", "pull", image],
                            f"Pulling image {image}" + (f" (attempt {attempt_num})" if attempt_num > 1 else ""),
                        )

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
                "--timeout=20m",
                "--wait",
                "--kubeconfig=/etc/rancher/k3s/k3s.yaml",
                *(f"--set={value}" for value in set_values_list),
            ],
            "Deploying Agent Stack platform with Helm",
        )

        if shas_guest_before and (
            replaced_digests := set(shas_guest_before.values())
            - set((await self._grab_image_shas(mode="guest")).values())
        ):
            for pod in dict.get(
                json.loads(
                    (
                        await self.run_in_vm(
                            ["k3s", "kubectl", "get", "pods", "-o", "json", "--all-namespaces"],
                            "Getting pods",
                        )
                    ).stdout
                ),
                "items",
                [],
            ):
                if any(
                    container_status.get("imageID", "") in replaced_digests
                    for container_status in pod.get("status", {}).get("containerStatuses", [])
                ):
                    await self.run_in_vm(
                        [
                            "k3s",
                            "kubectl",
                            "delete",
                            "pod",
                            pod["metadata"]["name"],
                            "-n",
                            pod["metadata"]["namespace"],
                        ],
                        f"Removing pod with obsolete image {pod['metadata']['namespace']}/{pod['metadata']['name']}",
                    )
