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

from beeai_server.configuration import Configuration
from beeai_server.domain.models.common import PaginatedResult
from beeai_server.domain.models.provider_build import BuildState, ProviderBuild
from beeai_server.domain.models.user import User
from beeai_server.exceptions import BuildAlreadyFinishedError, EntityNotFoundError, InvalidGithubReferenceError
from beeai_server.service_layer.build_manager import IProviderBuildManager
from beeai_server.service_layer.unit_of_work import IUnitOfWorkFactory
from beeai_server.utils.docker import DockerImageID
from beeai_server.utils.github import GithubUrl
from beeai_server.utils.logs_container import LogsContainer, ProcessLogMessage, ProcessLogType
from beeai_server.utils.utils import cancel_task

logger = logging.getLogger(__name__)


@inject
class ProviderBuildService:
    def __init__(self, build_manager: IProviderBuildManager, configuration: Configuration, uow: IUnitOfWorkFactory):
        self._uow = uow
        self._build_manager = build_manager
        self._config = configuration

    async def create_build(self, location: GithubUrl, user: User) -> ProviderBuild:
        from beeai_server.jobs.tasks.provider_build import build_provider as task

        try:
            version = await location.resolve_version()
        except ValueError as e:
            raise InvalidGithubReferenceError(str(e)) from e
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

        build = ProviderBuild(status=BuildState.MISSING, source=version, destination=destination, created_by=user.id)
        async with self._uow() as uow:
            await uow.provider_builds.create(provider_build=build)
            await task.configure(queueing_lock=str(build.id)).defer_async(provider_build_id=str(build.id))
            await uow.commit()
        return build

    async def get_build(self, provider_build_id: UUID) -> ProviderBuild:
        async with self._uow() as uow:
            return await uow.provider_builds.get(provider_build_id=provider_build_id)

    async def list_builds(self) -> PaginatedResult[ProviderBuild]:
        async with self._uow() as uow:
            return await uow.provider_builds.list_paginated()

    async def build_provider(self, provider_build_id: UUID):
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
            async with self._uow() as uow:
                await uow.provider_builds.update(provider_build=build)
                await uow.commit()
        except Exception as e:
            logger.warning(f"Failed to build provider: {e}")
            build.status = BuildState.FAILED
            async with self._uow() as uow:
                await uow.provider_builds.update(provider_build=build)
                await uow.commit()
            raise

    async def delete_build(self, provider_build_id: UUID):
        async with self._uow() as uow:
            build = await uow.provider_builds.get(provider_build_id=provider_build_id)
            if build.status not in {BuildState.FAILED, BuildState.COMPLETED}:
                with suppress(EntityNotFoundError):
                    await self._build_manager.cancel_job(provider_build_id=provider_build_id)
            await uow.provider_builds.delete(provider_build_id=provider_build_id)
            await uow.commit()

    async def stream_logs(self, provider_build_id: UUID) -> Callable[..., AsyncIterator[str]]:
        logs_container = LogsContainer()

        logs_task = asyncio.create_task(
            self._build_manager.stream_logs(provider_build_id=provider_build_id, logs_container=logs_container)
        )
        async with self._uow() as uow:
            build = await uow.provider_builds.get(provider_build_id=provider_build_id)
            if build.status in {BuildState.FAILED, BuildState.COMPLETED}:
                raise BuildAlreadyFinishedError(platform_build_id=build.id, state=build.status)

        async def watch_for_completion():
            state = BuildState.FAILED
            with suppress(Exception):
                state = await self._build_manager.wait_for_completion(provider_build_id=provider_build_id)
            logs_container.add(ProcessLogMessage(stream=ProcessLogType.STDOUT, message=f"Job {state}.", finished=True))

        watch_for_completion_task = asyncio.create_task(watch_for_completion())

        async def logs_iterator() -> AsyncIterator[str]:
            try:
                async with logs_container.stream() as stream:
                    async for message in stream:
                        if message.model_dump().get("error"):
                            raise RuntimeError(f"Error capturing logs: {message.message}")
                        yield json.dumps(message.model_dump(mode="json"))
                        if message.model_dump().get("finished"):
                            return
            finally:
                await cancel_task(logs_task)
                await cancel_task(watch_for_completion_task)

        return logs_iterator
