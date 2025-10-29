# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from collections.abc import AsyncIterator, Callable
from datetime import timedelta
from uuid import UUID

from a2a.types import AgentCard
from fastapi import HTTPException
from kink import inject
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from agentstack_server.domain.constants import SELF_REGISTRATION_EXTENSION_URI
from agentstack_server.domain.models.provider import (
    DockerImageProviderLocation,
    Provider,
    ProviderDeploymentState,
    ProviderLocation,
    ProviderWithState,
    UnmanagedState,
)
from agentstack_server.domain.models.registry import RegistryLocation
from agentstack_server.domain.models.user import User, UserRole
from agentstack_server.domain.repositories.env import EnvStoreEntity
from agentstack_server.exceptions import ManifestLoadError
from agentstack_server.service_layer.deployment_manager import (
    IProviderDeploymentManager,
)
from agentstack_server.service_layer.unit_of_work import IUnitOfWorkFactory
from agentstack_server.utils.a2a import get_extension
from agentstack_server.utils.github import ResolvedGithubUrl
from agentstack_server.utils.logs_container import LogsContainer
from agentstack_server.utils.utils import cancel_task, utc_now

logger = logging.getLogger(__name__)


@inject
class ProviderService:
    def __init__(self, deployment_manager: IProviderDeploymentManager, uow: IUnitOfWorkFactory):
        self._uow = uow
        self._deployment_manager = deployment_manager

    async def create_provider(
        self,
        *,
        user: User,
        location: ProviderLocation,
        origin: str | ResolvedGithubUrl | None = None,
        auto_stop_timeout: timedelta,
        registry: RegistryLocation | None = None,
        agent_card: AgentCard | None = None,
        variables: dict[str, str] | None = None,
    ) -> ProviderWithState:
        try:
            if not agent_card:
                agent_card = await location.load_agent_card()
            version_info = await location.get_version_info()

            if isinstance(origin, ResolvedGithubUrl):
                version_info.github = origin
                origin = origin.base

            provider = Provider(
                source=location,
                origin=origin or location.origin,
                registry=registry,
                version_info=version_info,
                agent_card=agent_card,
                created_by=user.id,
                auto_stop_timeout=auto_stop_timeout,
            )
            if not provider.managed and get_extension(agent_card, SELF_REGISTRATION_EXTENSION_URI):
                provider.unmanaged_state = UnmanagedState.ONLINE

        except ValueError as ex:
            raise ManifestLoadError(location=location, message=str(ex), status_code=HTTP_400_BAD_REQUEST) from ex
        except Exception as ex:
            raise ManifestLoadError(location=location, message=str(ex)) from ex

        async with self._uow() as uow:
            await uow.providers.create(provider=provider)
            if variables:
                await uow.env.update(
                    parent_entity=EnvStoreEntity.PROVIDER, parent_entity_id=provider.id, variables=variables
                )
            await uow.commit()
        [provider_response] = await self._get_providers_with_state(providers=[provider])
        return provider_response

    async def patch_provider(
        self,
        *,
        provider_id: UUID,
        user: User,
        location: ProviderLocation | None = None,
        auto_stop_timeout: timedelta | None = None,
        origin: str | ResolvedGithubUrl | None = None,
        agent_card: AgentCard | None = None,
        variables: dict[str, str] | None = None,
        allow_registry_update: bool = False,
        force: bool = False,
    ) -> ProviderWithState:
        user_id = user.id if user.role != UserRole.ADMIN else None

        github_version_info: ResolvedGithubUrl | None = None
        if isinstance(origin, ResolvedGithubUrl):
            github_version_info = origin
            origin = origin.base

        async with self._uow() as uow:
            provider = await uow.providers.get(provider_id=provider_id, user_id=user_id)
            if provider.registry and not allow_registry_update:
                raise ValueError("Cannot update provider added from registry")
            old_variables = (
                await uow.env.get_all(
                    parent_entity=EnvStoreEntity.PROVIDER,
                    parent_entity_ids=[provider.id],
                )
            )[provider.id]

        variables = old_variables if variables is None else variables

        updated_provider = provider.model_copy()
        updated_provider.source = location or updated_provider.source
        updated_provider.agent_card = agent_card or updated_provider.agent_card
        updated_provider.origin = origin or updated_provider.source.origin

        if auto_stop_timeout is not None:
            updated_provider.auto_stop_timeout = auto_stop_timeout

        # this is a bit heuristic, self-registered agents send a card in this format, but technically somebody else
        # can send it without the agent actually being online
        if agent_card and get_extension(agent_card, SELF_REGISTRATION_EXTENSION_URI):
            updated_provider.unmanaged_state = UnmanagedState.ONLINE

        # Some migrated docker providers may not have a docker version_info field, update during the patch
        if (
            isinstance(updated_provider.source, DockerImageProviderLocation)
            and updated_provider.version_info.docker is None
        ):
            updated_provider.version_info = await provider.source.get_version_info()

        if location is not None and location != provider.source:
            updated_provider.version_info = await location.get_version_info()

            if not agent_card:
                try:
                    updated_provider.agent_card = await location.load_agent_card()
                except ValueError as ex:
                    raise ManifestLoadError(
                        location=location, message=str(ex), status_code=HTTP_400_BAD_REQUEST
                    ) from ex
                except Exception as ex:
                    raise ManifestLoadError(location=location, message=str(ex)) from ex

        if github_version_info:
            updated_provider.version_info.github = github_version_info

        should_update = provider != updated_provider or variables != old_variables or force
        if not should_update:
            return (await self._get_providers_with_state(providers=[provider]))[0]

        updated_provider.updated_at = utc_now()

        async with self._uow() as uow:
            await uow.providers.update(provider=updated_provider)

            if old_variables != variables:
                await uow.env.delete(parent_entity=EnvStoreEntity.PROVIDER, parent_entity_id=provider_id)
                await uow.env.update(
                    parent_entity=EnvStoreEntity.PROVIDER, parent_entity_id=provider_id, variables=variables
                )
            # Rotate the provider (inside the transaction)
            await self._rotate_provider(provider=updated_provider, env=variables)
            await uow.commit()
        [provider_response] = await self._get_providers_with_state(providers=[updated_provider])
        return provider_response

    async def preview_provider(
        self, location: ProviderLocation, agent_card: AgentCard | None = None
    ) -> ProviderWithState:
        try:
            if not agent_card:
                agent_card = await location.load_agent_card()
            provider = Provider(
                source=location,
                origin=location.origin,
                version_info=await location.get_version_info(),
                agent_card=agent_card,
                created_by=uuid.uuid4(),
            )
            [provider_response] = await self._get_providers_with_state(providers=[provider])
            return provider_response
        except ValueError as ex:
            raise ManifestLoadError(location=location, message=str(ex), status_code=HTTP_400_BAD_REQUEST) from ex
        except Exception as ex:
            raise ManifestLoadError(location=location, message=str(ex)) from ex

    async def _get_providers_with_state(self, providers: list[Provider]) -> list[ProviderWithState]:
        result_providers = []
        provider_states = await self._deployment_manager.state(provider_ids=[provider.id for provider in providers])

        async with self._uow() as uow:
            provider_ids = [provider.id for provider in providers]
            providers_env = await uow.env.get_all(parent_entity=EnvStoreEntity.PROVIDER, parent_entity_ids=provider_ids)

            for provider, state in zip(providers, provider_states, strict=False):
                final_state = state
                if not provider.managed:
                    final_state = provider.unmanaged_state if provider.unmanaged_state else UnmanagedState.OFFLINE
                result_providers.append(
                    ProviderWithState(
                        **provider.model_dump(),
                        state=final_state,
                        missing_configuration=[
                            var
                            for var in provider.check_env(providers_env[provider.id], raise_error=False)
                            if var.required
                        ],
                    )
                )
        return result_providers

    async def delete_provider(self, *, provider_id: UUID, user: User) -> None:
        user_id = user.id if user.role != UserRole.ADMIN else None
        async with self._uow() as uow:
            provider = await uow.providers.get(provider_id=provider_id, user_id=user_id)
            await uow.providers.delete(provider_id=provider_id, user_id=user_id)
            if provider.managed:
                await self._deployment_manager.delete(provider_id=provider_id)
            await uow.commit()

    async def scale_down_providers(self):
        active_providers = [
            provider
            for provider in await self.list_providers()
            if provider.managed and provider.state == ProviderDeploymentState.RUNNING
        ]
        errors = []
        for provider in active_providers:
            try:
                if provider.auto_stop_timeout and (provider.last_active_at + provider.auto_stop_timeout) < utc_now():
                    logger.info(f"Scaling down provider: {provider.id}")
                    await self._deployment_manager.scale_down(provider_id=provider.id)
            except Exception as ex:
                errors.append(ex)
        if errors:
            raise ExceptionGroup("Exceptions occurred when scaling down providers", errors)

    async def remove_orphaned_providers(self):
        async with self._uow() as uow:
            existing_providers = [p.id async for p in uow.providers.list()]
        await self._deployment_manager.remove_orphaned_providers(existing_providers=existing_providers)

    async def list_providers(
        self, user: User | None = None, user_owned: bool | None = None, origin: str | None = None
    ) -> list[ProviderWithState]:
        # user_owned: True -> show user owned entities
        # user_owned: False -> show all but user owned entities
        # user_owned: None -> show all entities

        if user_owned is not None and user is None:
            raise ValueError("user_owned cannot be specified without a user")

        async with self._uow() as uow:
            return await self._get_providers_with_state(
                providers=[
                    p
                    async for p in uow.providers.list(
                        user_id=user.id if user_owned is True else None,
                        exclude_user_id=user.id if user_owned is False else None,
                        origin=origin,
                    )
                ]
            )

    async def get_provider(
        self, provider_id: UUID | None = None, location: ProviderLocation | None = None
    ) -> ProviderWithState:
        if not (bool(provider_id) ^ bool(location)):
            raise ValueError("Either provider_id or location must be provided")
        providers = [
            provider
            for provider in await self.list_providers()
            if provider.id == provider_id or provider.source == location
        ]
        if not providers:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"Provider with ID: {provider_id!s} not found")
        return providers[0]

    async def stream_logs(self, provider_id: UUID, user: User) -> Callable[..., AsyncIterator[str]]:
        user_id = user.id if user.role != UserRole.ADMIN else None
        async with self._uow() as uow:
            # check provider exists and user ownership
            await uow.providers.get(provider_id=provider_id, user_id=user_id)

        logs_container = LogsContainer()

        logs_task = asyncio.create_task(
            self._deployment_manager.stream_logs(provider_id=provider_id, logs_container=logs_container)
        )

        async def logs_iterator() -> AsyncIterator[str]:
            try:
                async with logs_container.stream() as stream:
                    async for message in stream:
                        if message.model_dump().get("error"):
                            raise RuntimeError(f"Error capturing logs: {message.message}")
                        yield json.dumps(message.model_dump(mode="json"))
            finally:
                await cancel_task(logs_task)

        return logs_iterator

    async def _rotate_provider(self, provider: Provider, env: dict[str, str]):
        [state] = await self._deployment_manager.state(provider_ids=[provider.id])
        if (
            provider.managed
            # provider is not idle (if idle, it will be updated next time it's scaled up)
            and state in {ProviderDeploymentState.RUNNING, ProviderDeploymentState.STARTING}
        ):
            await self._deployment_manager.create_or_replace(provider=provider, env=env)

    async def update_provider_env(
        self,
        *,
        provider_id: UUID,
        env: dict[str, str | None] | dict[str, str],
        user: User,
        allow_registry_update: bool = False,
    ) -> None:
        user_id = user.id if user.role != UserRole.ADMIN else None
        provider = None
        try:
            async with self._uow() as uow:
                provider = await uow.providers.get(provider_id=provider_id, user_id=user_id)
                if provider.registry and not allow_registry_update:
                    raise ValueError("Cannot update variables for a provider added from registry")
                await uow.env.update(parent_entity=EnvStoreEntity.PROVIDER, parent_entity_id=provider_id, variables=env)
                new_env = await uow.env.get_all(parent_entity=EnvStoreEntity.PROVIDER, parent_entity_ids=[provider_id])
                new_env = new_env[provider_id]
                # Rotate the provider (inside the transaction)
                await self._rotate_provider(provider=provider, env=new_env)
                await uow.commit()
        except Exception as ex:
            if not provider:
                return
            logger.error(f"Exception occurred while updating env, rolling back to previous state: {ex}")
            async with self._uow() as uow:
                orig_env = await uow.env.get_all(parent_entity=EnvStoreEntity.PROVIDER, parent_entity_ids=[provider_id])
                orig_env = orig_env[provider_id]
                try:
                    logger.exception(
                        f"Failed to update env, attempting to rollback provider: {provider.id} to previous state"
                    )
                    await self._deployment_manager.create_or_replace(provider=provider, env=orig_env)
                except Exception:
                    logger.error(f"Failed to rollback provider: {provider.id}")
            raise

    async def list_provider_env(self, *, provider_id: UUID, user: User) -> dict[str, str]:
        user_id = user.id if user.role != UserRole.ADMIN else None
        async with self._uow() as uow:
            await uow.providers.get(provider_id=provider_id, user_id=user_id)
            env = await uow.env.get_all(parent_entity=EnvStoreEntity.PROVIDER, parent_entity_ids=[provider_id])
            return env[provider_id]
