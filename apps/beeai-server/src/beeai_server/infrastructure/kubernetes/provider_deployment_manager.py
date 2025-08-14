# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import base64
import hashlib
import json
import logging
import re
from asyncio import TaskGroup
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager, suppress
from datetime import timedelta
from enum import StrEnum
from pathlib import Path
from typing import Any, Final
from uuid import UUID

import anyio
import kr8s
import yaml
from a2a.utils import AGENT_CARD_WELL_KNOWN_PATH
from httpx import AsyncClient, HTTPError
from jinja2 import Template
from kr8s.asyncio.objects import Deployment, Pod, Secret, Service
from pydantic import HttpUrl
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_delay, wait_fixed

from beeai_server.domain.models.provider import Provider, ProviderDeploymentState
from beeai_server.service_layer.deployment_manager import IProviderDeploymentManager, global_provider_variables
from beeai_server.utils.logs_container import LogsContainer, ProcessLogMessage, ProcessLogType
from beeai_server.utils.utils import extract_messages

logger = logging.getLogger(__name__)


class TemplateKind(StrEnum):
    deploy = "deploy"
    svc = "svc"
    secret = "secret"


TEMPLATE_KIND_TO_FILE_NAME: Final = {
    TemplateKind.deploy: "deployment.yaml",
    TemplateKind.svc: "service.yaml",
    TemplateKind.secret: "secret.yaml",
}

DEFAULT_TEMPLATE_DIR: Final = Path(__file__).parent / "default_templates"


class KubernetesProviderDeploymentManager(IProviderDeploymentManager):
    def __init__(
        self,
        api_factory: Callable[[], Awaitable[kr8s.asyncio.Api]],
        manifest_template_dir: Path | None = None,
    ):
        self._api_factory = api_factory
        self._create_lock = asyncio.Lock()
        self._template_dir = anyio.Path(manifest_template_dir or DEFAULT_TEMPLATE_DIR)
        self._templates: dict[TemplateKind, str] = {}

    @asynccontextmanager
    async def api(self) -> AsyncIterator[kr8s.asyncio.Api]:
        client = await self._api_factory()
        yield client

    async def _render_template(self, kind: TemplateKind, **variables) -> dict[str, Any]:
        if kind not in self._templates:
            self._templates[kind] = await (self._template_dir / TEMPLATE_KIND_TO_FILE_NAME[kind]).read_text()
        template = self._templates[kind]
        return yaml.safe_load(Template(template).render(**variables))

    def _get_k8s_name(self, provider_id: UUID, kind: TemplateKind | None = None):
        return f"beeai-provider-{provider_id}" + (f"-{kind}" if kind else "")

    def _get_provider_id_from_name(self, name: str, kind: TemplateKind | None = None) -> UUID:
        pattern = rf"beeai-provider-([0-9a-f-]+)-{kind}$" if kind else r"beeai-provider-([0-9a-f-]+)$"
        if match := re.match(pattern, name):
            [provider_id] = match.groups()
            return UUID(provider_id)
        raise ValueError(f"Invalid provider name format: {name}")

    def _get_env_for_provider(self, provider: Provider, env: dict[str, str | None]):
        return {**provider.extract_env(env), **global_provider_variables()}

    async def create_or_replace(self, *, provider: Provider, env: dict[str, str] | None = None) -> bool:
        if not provider.managed:
            raise ValueError("Attempted to update provider not managed by Kubernetes")

        async with self.api() as api:
            env = env or {}
            label = self._get_k8s_name(provider.id)

            service = Service(
                await self._render_template(
                    TemplateKind.svc,
                    provider_service_name=self._get_k8s_name(provider.id, kind=TemplateKind.svc),
                    provider_app_label=label,
                ),
                api=api,
            )
            env = self._get_env_for_provider(provider, env)
            secret = Secret(
                await self._render_template(
                    TemplateKind.secret,
                    provider_secret_name=self._get_k8s_name(provider.id, TemplateKind.secret),
                    provider_app_label=label,
                    secret_data={key: base64.b64encode(value.encode()).decode() for key, value in env.items()},
                ),
                api=api,
            )

            deployment_manifest = await self._render_template(
                TemplateKind.deploy,
                provider_deployment_name=self._get_k8s_name(provider.id, TemplateKind.deploy),
                provider_app_label=label,
                image=str(provider.source.root),
                provider_secret_name=self._get_k8s_name(provider.id, TemplateKind.secret),
            )
            combined_manifest = json.dumps(
                {"service": service.raw, "secret": secret.raw, "deployment": deployment_manifest}
            )
            deployment_hash = hashlib.sha256(combined_manifest.encode()).hexdigest()[:63]
            deployment_manifest["metadata"]["labels"]["deployment-hash"] = deployment_hash

            deployment = Deployment(deployment_manifest, api=api)
            async with self._create_lock:
                try:
                    existing_deployment = await Deployment.get(deployment.metadata.name, api=api)
                    if existing_deployment.metadata.labels["deployment-hash"] == deployment_hash:
                        if existing_deployment.replicas == 0:
                            await deployment.scale(1)
                            return True
                        return False  # Deployment was not modified
                    logger.info(f"Recreating deployment {deployment.metadata.name} due to configuration change")
                    await self.delete(provider_id=provider.id)
                except kr8s.NotFoundError:
                    logger.info(f"Creating new deployment {deployment.metadata.name}")
                try:
                    await secret.create()
                    await service.create()
                    await deployment.create()
                    await deployment.adopt(service)
                    await deployment.adopt(secret)
                except Exception as ex:
                    logger.error("Failed to create provider", exc_info=ex)
                    # Try to revert changes already made
                    with suppress(Exception):
                        await secret.delete()
                    with suppress(Exception):
                        await service.delete()
                    with suppress(Exception):
                        await deployment.delete()
                    raise
                return True

    async def delete(self, *, provider_id: UUID) -> None:
        with suppress(kr8s.NotFoundError):
            async with self.api() as api:
                deploy = await Deployment.get(name=self._get_k8s_name(provider_id, TemplateKind.deploy), api=api)
                await deploy.delete(propagation_policy="Foreground", force=True)
                await deploy.wait({"delete"})

    async def scale_down(self, *, provider_id: UUID) -> None:
        async with self.api() as api:
            deploy = await Deployment.get(name=self._get_k8s_name(provider_id, TemplateKind.deploy), api=api)
            await deploy.scale(0)

    async def scale_up(self, *, provider_id: UUID) -> None:
        async with self.api() as api:
            deploy = await Deployment.get(name=self._get_k8s_name(provider_id, TemplateKind.deploy), api=api)
            await deploy.scale(1)

    async def wait_for_startup(self, *, provider_id: UUID, timeout: timedelta) -> None:  # noqa: ASYNC109 (the timeout actually corresponds to kubernetes timeout)
        async with self.api() as api:
            deployment = await Deployment.get(name=self._get_k8s_name(provider_id, kind=TemplateKind.deploy), api=api)
            await deployment.wait("condition=Available", timeout=int(timeout.total_seconds()))
            # For some reason the first request sometimes doesn't come through
            # (the service does not route immediately after deploy is available?)
            async for attempt in AsyncRetrying(
                stop=stop_after_delay(timedelta(seconds=10)),
                wait=wait_fixed(timedelta(seconds=0.5)),
                retry=retry_if_exception_type(HTTPError),
                reraise=True,
            ):
                with attempt:
                    async with AsyncClient(
                        base_url=str(await self.get_provider_url(provider_id=provider_id))
                    ) as client:
                        resp = await client.get(AGENT_CARD_WELL_KNOWN_PATH, timeout=2)
                        resp.raise_for_status()

    async def state(self, *, provider_ids: list[UUID]) -> list[ProviderDeploymentState]:
        async with self.api() as api:
            deployments = {
                self._get_provider_id_from_name(deployment.metadata.name, TemplateKind.deploy): deployment
                async for deployment in kr8s.asyncio.get(
                    kind="deployment",
                    label_selector={"managedBy": "beeai-platform"},
                    api=api,
                )
            }
            provider_ids_set = set(provider_ids)
            deployments = {provider_id: d for provider_id, d in deployments.items() if provider_id in provider_ids_set}
            states = []
            for provider_id in provider_ids:
                deployment = deployments.get(provider_id)
                if not deployment:
                    state = ProviderDeploymentState.missing
                elif deployment.status.get("availableReplicas", 0) > 0:
                    state = ProviderDeploymentState.running
                elif deployment.status.get("replicas", 0) == 0:
                    state = ProviderDeploymentState.ready
                else:
                    state = ProviderDeploymentState.starting
                states.append(state)
            return states

    async def get_provider_url(self, *, provider_id: UUID) -> HttpUrl:
        return HttpUrl(f"http://{self._get_k8s_name(provider_id, TemplateKind.svc)}:8000")

    async def stream_logs(self, *, provider_id: UUID, logs_container: LogsContainer):
        try:
            async with self.api() as api:
                missing_logged = False
                while True:
                    try:
                        deploy = await Deployment.get(
                            name=self._get_k8s_name(provider_id, kind=TemplateKind.deploy),
                            api=api,
                        )
                        if pods := await deploy.pods():
                            break
                    except kr8s.NotFoundError:
                        ...
                    if not missing_logged:
                        logs_container.add_stdout("Provider is not running, run a query to start it up...")
                    missing_logged = True
                    await asyncio.sleep(1)

                if deploy.status.get("availableReplicas", 0) == 0:
                    async for _event_stream_type, event in api.watch(
                        kind="event",
                        # TODO: we select for only one pod, for multi-pod agents this might hold up the logs for a while
                        field_selector=f"involvedObject.name=={pods[0].name},involvedObject.kind==Pod",
                    ):
                        message = event.raw.get("message", "")
                        logs_container.add_stdout(f"{event.raw.reason}: {message}")
                        if event.raw.reason == "Started":
                            break

                for _ in range(10):
                    try:
                        _ = [log async for log in pods[0].logs(tail_lines=1)]
                        break
                    except kr8s.ServerError:
                        await asyncio.sleep(1)
                else:
                    logs_container.add_stdout("Container crashed or not starting up, attempting to get previous logs:")
                    with suppress(kr8s.ServerError):
                        previous_logs = [log async for log in pods[0].logs(previous=True)]
                        if previous_logs:
                            logs_container.add_stdout("Previous container logs:")
                            for log in previous_logs:
                                logs_container.add_stdout(f"Previous: {log}")
                    return

                # Stream logs from pods
                async def stream_logs(pod: Pod):
                    async for line in pod.logs(follow=True):
                        logs_container.add_stdout(
                            f"{pod.name.replace(self._get_k8s_name(provider_id, TemplateKind.deploy), '')}: {line}"
                        )

                async with TaskGroup() as tg:
                    for pod in await deploy.pods():
                        tg.create_task(stream_logs(pod))

        except Exception as ex:
            logs_container.add(
                ProcessLogMessage(stream=ProcessLogType.stderr, message=extract_messages(ex), error=True)
            )
            logger.error(f"Error while streaming logs: {extract_messages(ex)}")
            raise
