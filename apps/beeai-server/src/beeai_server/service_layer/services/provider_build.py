# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator, Callable
from contextlib import suppress
from datetime import timedelta
from uuid import UUID

from kink import inject
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_delay, wait_fixed

from beeai_server.api.schema.common import PaginationQuery
from beeai_server.configuration import Configuration
from beeai_server.domain.models.common import PaginatedResult
from beeai_server.domain.models.provider_build import (
    BuildState,
    NoAction,
    OnCompleteAction,
    ProviderBuild,
    UpdateProvider,
)
from beeai_server.domain.models.user import User, UserRole
from beeai_server.exceptions import (
    BuildAlreadyFinishedError,
    EntityNotFoundError,
    VersionResolveError,
)
from beeai_server.service_layer.build_manager import IProviderBuildManager
from beeai_server.service_layer.unit_of_work import IUnitOfWorkFactory
from beeai_server.utils.docker import DockerImageID
from beeai_server.utils.github import GithubUrl, ResolvedGithubUrl
from beeai_server.utils.logs_container import LogsContainer, ProcessLogMessage
from beeai_server.utils.utils import cancel_task

logger = logging.getLogger(__name__)


@inject
class ProviderBuildService:
    def __init__(self, build_manager: IProviderBuildManager, configuration: Configuration, uow: IUnitOfWorkFactory):
        self._uow = uow
        self._build_manager = build_manager
        self._config = configuration

    async def _resolve_version(self, location: GithubUrl) -> tuple[ResolvedGithubUrl, DockerImageID]:
        try:
            version = await location.resolve_version()
        except Exception as e:
            raise VersionResolveError(str(location), str(e)) from e
        if not self._config.provider_build.oci_build_registry_prefix:
            raise RuntimeError("OCI build registry is not configured")

        destination = DockerImageID(
            root=self._config.provider_build.image_format.format(
                registry_prefix=self._config.provider_build.oci_build_registry_prefix.lower(),
                org=version.org.lower(),
                repo=version.repo.lower(),
                path=(version.path.replace("/", "-") if version.path else "agent").lower(),
                commit_hash=version.commit_hash.lower(),
            )
        )
        return version, destination

    async def preview_build(
        self, location: GithubUrl, user: User, on_complete: OnCompleteAction | None = None
    ) -> ProviderBuild:
        version, destination = await self._resolve_version(location)
        return ProviderBuild(
            status=BuildState.MISSING,
            source=version,
            destination=destination,
            created_by=user.id,
            on_complete=on_complete or NoAction(),
        )

    async def create_build(
        self, location: GithubUrl, user: User, on_complete: OnCompleteAction | None = None
    ) -> ProviderBuild:
        from beeai_server.jobs.tasks.provider_build import build_provider as task

        version, destination = await self._resolve_version(location)

        build = ProviderBuild(
            status=BuildState.MISSING,
            source=version,
            destination=destination,
            created_by=user.id,
            on_complete=on_complete or NoAction(),
        )
        async with self._uow() as uow:
            match on_complete:
                case UpdateProvider(provider_id=provider_id):
                    # check permissions to update
                    _ = await uow.providers.get(provider_id=provider_id, user_id=user.id)

            await uow.provider_builds.create(provider_build=build)
            await task.configure(queueing_lock=str(build.id)).defer_async(provider_build_id=str(build.id))
            await uow.commit()
        return build

    async def update_build(self, *, provider_build: ProviderBuild):
        async with self._uow() as uow:
            await uow.provider_builds.update(provider_build=provider_build)
            await uow.commit()

    async def get_build(self, provider_build_id: UUID) -> ProviderBuild:
        async with self._uow() as uow:
            return await uow.provider_builds.get(provider_build_id=provider_build_id)

    async def list_builds(
        self, pagination: PaginationQuery, status: BuildState | None = None, user: User | None = None
    ) -> PaginatedResult[ProviderBuild]:
        user_id = user.id if user else None
        async with self._uow() as uow:
            return await uow.provider_builds.list_paginated(
                user_id=user_id,
                limit=pagination.limit,
                page_token=pagination.page_token,
                order=pagination.order,
                order_by=pagination.order_by,
                status=status,
            )

    async def build_provider(self, provider_build_id: UUID) -> ProviderBuild:
        async with self._uow() as uow:
            build = await uow.provider_builds.get(provider_build_id=provider_build_id)
            if build.status != BuildState.MISSING:
                raise RuntimeError("Build already started or completed")
            try:
                build.status = await self._build_manager.create_job(
                    provider_build=build,
                    job_timeout=timedelta(seconds=self._config.provider_build.job_timeout_sec),
                )
            except Exception as e:
                logger.warning(f"Failed to build provider: {e}")
                build.status = BuildState.FAILED
                raise
            finally:
                await uow.provider_builds.update(provider_build=build)
                await uow.commit()

        try:
            # This can take very long, opening transaction after
            build.status = await self._build_manager.wait_for_completion(provider_build_id=build.id)
            if build.status == BuildState.FAILED:
                build.error_message = "Build Job failed, please retry and watch log stream for more details"
            async with self._uow() as uow:
                await uow.provider_builds.update(provider_build=build)
                await uow.commit()
            return build
        except Exception as e:
            logger.warning(f"Failed to build provider: {e}")
            build.status = BuildState.FAILED
            build.error_message = str(e)
            async with self._uow() as uow:
                await uow.provider_builds.update(provider_build=build)
                await uow.commit()
            raise

    async def delete_build(self, provider_build_id: UUID, user: User):
        user_id = user.id if user.role != UserRole.ADMIN else None
        async with self._uow() as uow:
            build = await uow.provider_builds.get(provider_build_id=provider_build_id, user_id=user_id)
            if build.status not in {BuildState.FAILED, BuildState.COMPLETED}:
                with suppress(EntityNotFoundError):
                    await self._build_manager.cancel_job(provider_build_id=provider_build_id)
            await uow.provider_builds.delete(provider_build_id=provider_build_id, user_id=user_id)
            await uow.commit()

    async def stream_logs(
        self,
        provider_build_id: UUID,
        user: User,
        wait_for_start_timeout: timedelta = timedelta(minutes=5),
    ) -> Callable[..., AsyncIterator[str]]:
        logs_container = LogsContainer()
        user_id = user.id if user.role != UserRole.ADMIN else None
        async with self._uow() as uow:
            build = await uow.provider_builds.get(provider_build_id=provider_build_id, user_id=user_id)
            if build.status in {BuildState.FAILED, BuildState.COMPLETED}:
                raise BuildAlreadyFinishedError(platform_build_id=build.id, state=build.status)

        logs_task = asyncio.create_task(
            self._build_manager.stream_logs(provider_build_id=provider_build_id, logs_container=logs_container)
        )

        async def watch_for_completion():
            logs_container.add_stdout("Waiting for build job to be scheduled...")
            state = BuildState.FAILED
            on_complete = NoAction()
            try:
                async for attempt in AsyncRetrying(
                    stop=stop_after_delay(wait_for_start_timeout),
                    wait=wait_fixed(timedelta(seconds=2)),
                    retry=retry_if_exception_type(EntityNotFoundError),
                    reraise=True,
                ):
                    with attempt:
                        async with self._uow() as uow:
                            # If the build or worker fails to deploy the job, the wait would get stuck retrying
                            # waiting for a k8s job that will never be created. Hence, we check database state:
                            build = await uow.provider_builds.get(provider_build_id=provider_build_id)
                            on_complete = build.on_complete
                            if build.status in {BuildState.FAILED, BuildState.COMPLETED}:
                                state = build.status
                                break
                        state = await self._build_manager.wait_for_completion(provider_build_id=provider_build_id)
            except EntityNotFoundError:
                message = (
                    "Wait timeout for job to be scheduled exceeded, the job queue might be busy at the moment."
                    "The job will continue to run in the background when the queue is available."
                )
                logs_container.add(ProcessLogMessage(message=message, error=True))
                return

            # Wait for post-build action to complete
            if state == BuildState.BUILD_COMPLETED:
                logs_container.add_stdout(f"Processing post-build action: {on_complete.type}")
                await asyncio.sleep(0.5)
                try:
                    async with asyncio.timeout(timedelta(seconds=10).total_seconds()):
                        while True:
                            async with self._uow() as uow:
                                build = await uow.provider_builds.get(provider_build_id=provider_build_id)
                                if build.status in {BuildState.FAILED, BuildState.COMPLETED}:
                                    break
                            await asyncio.sleep(1)
                except TimeoutError:
                    logs_container.add(ProcessLogMessage(message="Waiting for action timed out.", error=True))
            logs_container.add(ProcessLogMessage(message=f"Job {state}.", finished=True))

        watch_for_completion_task = asyncio.create_task(watch_for_completion())

        async def logs_iterator() -> AsyncIterator[str]:
            try:
                async with logs_container.stream() as stream:
                    async for message in stream:
                        if message.model_dump().get("error"):
                            raise RuntimeError(f"Error capturing logs: {message.message}")
                        yield json.dumps(message.model_dump(mode="json"))
                        message_dict = message.model_dump()
                        if message_dict.get("finished") or message_dict.get("error"):
                            return
            finally:
                await cancel_task(logs_task)
                await cancel_task(watch_for_completion_task)

        return logs_iterator
