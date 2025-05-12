# Copyright 2025 © BeeAI a Series of LF Projects, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import json
import logging
from contextlib import suppress
from typing import AsyncIterator, Callable, Coroutine, overload

import anyio
from fastapi import HTTPException
from kink import inject
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from beeai_server.adapters.interface import IProviderRepository, IEnvVariableRepository, IContainerBackend
from beeai_server.custom_types import ID
from beeai_server.domain.provider.model import (
    ProviderLocation,
    Agent,
    BaseProvider,
    ProviderStatus,
    ProviderErrorMessage,
)
from beeai_server.domain.provider.container import (
    ProviderContainer,
    LoadedProvider,
)
from beeai_server.domain.registry import RegistryLocation
from beeai_server.schema import ProviderWithStatus
from beeai_server.exceptions import ManifestLoadError
from beeai_server.utils.docker import DockerImageID
from beeai_server.utils.logs_container import LogsContainer

logger = logging.getLogger(__name__)


@inject
class ProviderService:
    def __init__(
        self,
        provider_repository: IProviderRepository,
        loaded_provider_container: ProviderContainer,
        env_repository: IEnvVariableRepository,
    ):
        self._repository = provider_repository
        self._loaded_provider_container = loaded_provider_container
        self._env_repository = env_repository

    @inject
    async def import_image(
        self, *, data: AsyncIterator[bytes], image_id: DockerImageID, container_backend: IContainerBackend
    ):
        await container_backend.import_image(data=data, image_id=image_id)

    @inject
    async def check_image(self, *, image_hash: str, container_backend: IContainerBackend):
        if not await container_backend.check_image(image=image_hash):
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"Image with ID: {str(image_hash)} not found")

    async def register_provider(
        self, *, location: ProviderLocation, registry: RegistryLocation | None = None, persist: bool = True
    ) -> ProviderWithStatus:
        try:
            provider = await location.load(registry=registry, persistent=persist)
            all_agents = {a.name for a in await self.list_agents()}
            provider_agents = {a.name for a in provider.manifest.agents}
            env = await self._env_repository.get_all()
            if would_override := set(provider_agents) & set(all_agents):
                loaded_providers = self._loaded_provider_container.loaded_providers.values()
                loaded_persistent_agents = {a.name for p in loaded_providers if p.provider.persistent for a in p.agents}
                if duplicate_agents := set(provider_agents) & set(loaded_persistent_agents):
                    raise ValueError(f"Duplicate agents: {duplicate_agents} are already registered to the platform.")
                else:
                    logger.warning(f"Overriding unpersisted agents: {would_override}")
            if persist:
                await self._repository.create(provider=provider)
        except ValueError as ex:
            raise ManifestLoadError(location=location, message=str(ex), status_code=HTTP_400_BAD_REQUEST) from ex
        except Exception as ex:
            raise ManifestLoadError(location=location, message=str(ex)) from ex
        await self._loaded_provider_container.add_or_replace(provider)
        return self._get_providers_with_status(providers=[provider], env=env)[0]

    async def preview_provider(self, location: ProviderLocation):
        try:
            provider = await location.load()
            env = await self._env_repository.get_all()
            return self._get_providers_with_status(providers=[provider], env=env)[0]
        except ValueError as ex:
            raise ManifestLoadError(location=location, message=str(ex), status_code=HTTP_400_BAD_REQUEST) from ex
        except Exception as ex:
            raise ManifestLoadError(location=location, message=str(ex)) from ex

    def _get_providers_with_status(
        self, providers: list[BaseProvider], env: dict[str, str]
    ) -> list[ProviderWithStatus]:
        result_providers = []
        for provider in providers:
            if loaded_provider := self._loaded_provider_container.loaded_providers.get(provider.id, None):
                result_providers.append(
                    ProviderWithStatus(
                        **provider.model_dump(),
                        status=loaded_provider.status,
                        last_error=loaded_provider.last_error,
                        missing_configuration=[var for var in loaded_provider.missing_configuration if var.required],
                    )
                )
            else:
                result_providers.append(
                    ProviderWithStatus(
                        **provider.model_dump(),
                        status=ProviderStatus.not_loaded,
                        missing_configuration=[
                            var for var in provider.check_env(env, raise_error=False) if var.required
                        ],
                        last_error=ProviderErrorMessage(message="Provider not yet initialized"),
                    )
                )
        return result_providers

    @overload
    async def install_provider(
        self, *, id: ID | None = None, location: ProviderLocation | None = None, stream: True
    ) -> Callable[..., AsyncIterator[str]]: ...

    @overload
    async def install_provider(
        self, *, id: ID | None = None, location: ProviderLocation | None = None, stream: False = False
    ) -> Callable[..., Coroutine[..., None, None]]: ...

    async def install_provider(
        self, *, id: ID | None = None, location: ProviderLocation | None = None, stream: bool = False
    ) -> Callable[..., AsyncIterator[str] | Coroutine[..., None, None]]:
        if not (bool(id) ^ bool(location)):
            raise ValueError("Either id or location must be provided")

        logs_container = LogsContainer()
        if id:
            provider = await self.get_provider(id=id)
            if provider.id not in self._loaded_provider_container.loaded_providers:
                raise ValueError("Provider is not loaded")

            async def _install():
                await self._loaded_provider_container.loaded_providers[id].install(logs_container=logs_container)
        else:
            source = await location.get_source()

            async def _install():
                await source.install(logs_container=logs_container)
                await self.register_provider(location=location)

        if stream:

            async def logs_iterator() -> AsyncIterator[str]:
                async with anyio.create_task_group() as task_group:

                    async def cancel_on_finish(coro):
                        await coro
                        task_group.cancel_scope.cancel()

                    task_group.start_soon(cancel_on_finish, _install())

                    async with logs_container.stream() as stream:
                        async for message in stream:
                            yield json.dumps(message.model_dump(mode="json"))

            return logs_iterator

        return _install

    async def delete_provider(self, *, id: ID, force: bool = False):
        provider = await self.get_provider(id=id)
        provider = self._loaded_provider_container.loaded_providers[provider.id]

        if getattr(provider.provider, "registry", None) and not force:
            await provider.uninstall()
        else:
            await provider.uninstall()
            with suppress(ValueError):  # unpersisted providers are not found in repository
                await self._repository.delete(provider_id=id)
            await self._loaded_provider_container.remove(provider)

    async def _get_all_providers(self) -> list[BaseProvider]:
        persisted_providers = {provider.id: provider for provider in await self._repository.list()}
        loaded_providers = {p_id: p.provider for p_id, p in self._loaded_provider_container.loaded_providers.items()}
        return list((persisted_providers | loaded_providers).values())

    async def list_providers(self) -> list[ProviderWithStatus]:
        return self._get_providers_with_status(
            providers=await self._get_all_providers(),
            env=await self._env_repository.get_all(),
        )

    async def get_provider(self, id: ID) -> ProviderWithStatus:
        providers = [provider for provider in await self.list_providers() if provider.id == id]
        if not providers:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"Provider with ID: {str(id)} not found")
        return providers[0]

    async def list_agents(self) -> list[Agent]:
        return [
            agent for provider in self._loaded_provider_container.loaded_providers.values() for agent in provider.agents
        ]

    async def stream_logs(self, id: ID) -> Callable[..., AsyncIterator[str]]:
        if not (provider := self._loaded_provider_container.loaded_providers.get(id, None)):
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Provider not found")

        async def logs_iterator() -> AsyncIterator[str]:
            async with provider.logs_container.stream() as stream:
                async for message in stream:
                    yield json.dumps(message.model_dump(mode="json"))

        return logs_iterator

    async def get_provider_by_agent_name(self, *, agent_name: str) -> LoadedProvider:
        try:
            return self._loaded_provider_container.get_provider_by_agent(agent_name=agent_name)
        except ValueError as ex:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"Agent {agent_name} not found") from ex

    async def get_provider_by_run_id(self, *, run_id: str) -> LoadedProvider:
        try:
            return self._loaded_provider_container.get_provider_by_run(run_id=run_id)
        except ValueError as ex:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"Run {run_id} not found") from ex
