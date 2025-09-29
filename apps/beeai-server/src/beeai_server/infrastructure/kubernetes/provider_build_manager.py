# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import base64
import logging
import re
from asyncio import TaskGroup
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager, suppress
from datetime import timedelta
from pathlib import Path
from typing import Any, Final, cast
from uuid import UUID

import anyio
import kr8s
import yaml
from jinja2 import Template
from kr8s.asyncio.objects import Job, Pod, Secret
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_delay, wait_fixed

from beeai_server.configuration import Configuration
from beeai_server.domain.models.provider_build import BuildState, ProviderBuild
from beeai_server.exceptions import EntityNotFoundError
from beeai_server.service_layer.build_manager import IProviderBuildManager
from beeai_server.utils.logs_container import LogsContainer, ProcessLogMessage, ProcessLogType
from beeai_server.utils.utils import extract_messages

logger = logging.getLogger(__name__)


BUILD_AGENT_JOB_FILE_NAME: Final = "build-provider-job.yaml"
BUILD_AGENT_GITHUB_SECRET_NAME: Final = "build-provider-secret.yaml"
DEFAULT_TEMPLATE_DIR: Final = Path(__file__).parent / "default_templates"


class KubernetesProviderBuildManager(IProviderBuildManager):
    def __init__(
        self,
        configuration: Configuration,
        api_factory: Callable[[], Awaitable[kr8s.asyncio.Api]],
        manifest_template_dir: Path | None = None,
    ):
        self._api_factory = api_factory
        self._create_lock = asyncio.Lock()
        self._template_dir = anyio.Path(manifest_template_dir or DEFAULT_TEMPLATE_DIR)
        self._template = None
        self._secret_template = None
        self._configuration = configuration

    @asynccontextmanager
    async def api(self) -> AsyncIterator[kr8s.asyncio.Api]:
        client = await self._api_factory()
        yield client

    async def _render_template(self, **variables) -> dict[str, Any]:
        if self._template is None:
            self._template = await (self._template_dir / BUILD_AGENT_JOB_FILE_NAME).read_text()
        return yaml.safe_load(Template(self._template).render(**variables))

    async def _render_secret_template(self, **variables) -> dict[str, Any]:
        if self._secret_template is None:
            self._secret_template = await (self._template_dir / BUILD_AGENT_GITHUB_SECRET_NAME).read_text()
        return yaml.safe_load(Template(self._secret_template).render(**variables))

    def _get_k8s_name(self, provider_build_id: UUID):
        return f"beeai-build-{provider_build_id}"

    def _get_build_id_from_name(self, name: str) -> UUID:
        pattern = r"beeai-build-([0-9a-f-]+)$"
        if match := re.match(pattern, name):
            [provider_build_id] = match.groups()
            return UUID(provider_build_id)
        raise ValueError(f"Invalid provider name format: {name}")

    def _get_build_status(self, job: Job | None) -> BuildState:
        if not job:
            return BuildState.MISSING
        conditions = job.status.get("conditions", [])
        for condition in conditions:
            if condition.get("type") == "Complete" and condition.get("status") == "True":
                return BuildState.COMPLETED
            elif condition.get("type") == "Failed" and condition.get("status") == "True":
                return BuildState.FAILED
        return BuildState.IN_PROGRESS

    async def create_job(
        self, *, provider_build: ProviderBuild, job_timeout: timedelta = timedelta(minutes=20)
    ) -> BuildState:
        async with self.api() as api:
            name = self._get_k8s_name(provider_build.id)
            secret = None
            if github_token := await provider_build.source.get_github_token():
                secret = Secret(
                    await self._render_secret_template(
                        git_token_secret_name=f"{name}-secret",
                        provider_build_label=name,
                        secret_data={"GIT_TOKEN": base64.b64encode(f"x-access-token:{github_token}".encode()).decode()},
                    ),
                    api=api,
                )

            job = Job(
                await self._render_template(
                    job_timeout_seconds=int(job_timeout.total_seconds()),
                    provider_build_name=name,
                    provider_build_label=name,
                    git_host=provider_build.source.host,
                    git_host_upper=provider_build.source.host.upper(),
                    git_org=provider_build.source.org,
                    git_repo=provider_build.source.repo,
                    git_path=provider_build.source.path or ".",
                    git_ref=provider_build.source.commit_hash,
                    destination=str(provider_build.destination),
                    git_token_secret_name=f"{name}-secret",
                ),
                api=api,
            )
            try:
                if secret:
                    await secret.create()
                await job.create()
                if secret:
                    await job.adopt(secret)
            except Exception as ex:
                logger.error("Failed to create build job", exc_info=ex)
                if secret:
                    with suppress(Exception):
                        await secret.delete()
                with suppress(Exception):
                    await job.delete()
                raise

            return BuildState.IN_PROGRESS

    async def wait_for_completion(self, *, provider_build_id: UUID) -> BuildState:
        async with self.api() as api:
            try:
                job = await Job.get(name=self._get_k8s_name(provider_build_id), api=api)
                await job.wait(["condition=Complete", "condition=Failed"])
                return self._get_build_status(job)
            except kr8s.NotFoundError as e:
                raise EntityNotFoundError("build_provider_job", provider_build_id) from e

    async def cancel_job(self, *, provider_build_id: UUID, grace_period: timedelta = timedelta(seconds=20)) -> None:
        async with self.api() as api:
            try:
                job = await Job.get(name=self._get_k8s_name(provider_build_id), api=api)
                await job.delete(grace_period=int(grace_period.total_seconds()))
            except kr8s.NotFoundError as e:
                raise EntityNotFoundError("build_provider_job", provider_build_id) from e

    async def state(self, *, provider_build_ids: list[UUID]) -> dict[UUID, BuildState]:
        async with self.api() as api:
            jobs = {
                self._get_build_id_from_name(job.metadata.name): cast(Job, job)
                async for job in kr8s.asyncio.get(kind="job", label_selector={"managedBy": "beeai-platform"}, api=api)
            }
            return {build_id: self._get_build_status(jobs.get(build_id)) for build_id in provider_build_ids}

    async def stream_logs(
        self, *, provider_build_id: UUID, logs_container: LogsContainer, wait_timeout: timedelta = timedelta(minutes=10)
    ) -> None:
        try:
            async with self.api() as api:
                missing_logged = False
                while True:
                    try:
                        # Get pods for this job
                        pods = [
                            cast(Pod, pod)
                            async for pod in kr8s.asyncio.get(
                                kind="pod",
                                label_selector={"job-name": self._get_k8s_name(provider_build_id)},
                                api=api,
                            )
                        ]
                        if pods:
                            break
                    except kr8s.NotFoundError:
                        ...
                    if not missing_logged:
                        logs_container.add_stdout("Build job is not running...")
                    missing_logged = True
                    await asyncio.sleep(1)

                pod = pods[0]

                async def stream_container_logs(container_name: str):
                    async for attempt in AsyncRetrying(
                        stop=stop_after_delay(wait_timeout),
                        wait=wait_fixed(timedelta(seconds=1)),
                        retry=retry_if_exception_type(kr8s.ServerError),
                        reraise=True,
                    ):
                        with attempt:
                            # Test if we can get logs (even just 1 line)
                            _ = [log async for log in pod.logs(container=container_name, tail_lines=1)]

                    logs_container.add_stdout(f"[{container_name}]: Starting log stream...")
                    try:
                        async for line in pod.logs(container=container_name, follow=True):
                            logs_container.add_stdout(f"[{container_name}]: {line}")
                    except kr8s.ServerError as e:
                        logs_container.add_stdout(f"[{container_name}]: Log streaming ended: {e}")
                    except Exception as e:
                        logs_container.add_stdout(f"[{container_name}]: Unexpected error during streaming: {e}")

                # Get container names from pod spec (init containers + regular containers)
                containers = pod.spec.get("initContainers", []) + pod.spec.get("containers", [])
                async with TaskGroup() as tg:
                    for container in containers:
                        tg.create_task(stream_container_logs(container["name"]))

        except Exception as ex:
            logs_container.add(
                ProcessLogMessage(stream=ProcessLogType.STDERR, message=extract_messages(ex), error=True)
            )
            logger.error(f"Error while streaming logs: {extract_messages(ex)}")
            raise
