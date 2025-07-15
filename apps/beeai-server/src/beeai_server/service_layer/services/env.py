# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging

from kink import inject

from beeai_server.domain.models.provider import ProviderDeploymentState
from beeai_server.service_layer.deployment_manager import IProviderDeploymentManager, global_provider_variables
from beeai_server.service_layer.unit_of_work import IUnitOfWorkFactory

logger = logging.getLogger(__name__)


@inject
class EnvService:
    def __init__(
        self,
        uow: IUnitOfWorkFactory,
        deployment_manager: IProviderDeploymentManager,
    ):
        self._uow = uow
        self._deployment_manager = deployment_manager

    async def update_env(self, *, env: dict[str, str | None]):
        affected_providers = []
        global_vars = global_provider_variables()
        try:
            async with self._uow() as uow:
                await uow.env.update(env)
                new_env = await uow.env.get_all()
                providers = [provider async for provider in uow.providers.list()]
                provider_states = await self._deployment_manager.state(provider_ids=[p.id for p in providers])
                for provider, state in zip(providers, provider_states, strict=True):
                    if (
                        provider.managed
                        # provider is not idle (if idle, it will be updated next time it's scaled up)
                        and state in {ProviderDeploymentState.running, ProviderDeploymentState.starting}
                        # env of this provider was touched
                        and env.keys() & {e.name for e in provider.env} - global_vars.keys()
                    ):
                        affected_providers.append(provider)
                        # Rotate the provider (inside the transaction)
                        await self._deployment_manager.create_or_replace(provider=provider, env=new_env)
                await uow.commit()
        except Exception as ex:
            logger.error(f"Exception occurred while updating env, rolling back to previous state: {ex}")
            async with self._uow() as uow:
                orig_env = await uow.env.get_all()
                for provider in affected_providers:
                    try:
                        logger.exception(
                            f"Failed to update env, attempting to rollback provider: {provider.id} to previous state"
                        )
                        await self._deployment_manager.create_or_replace(provider=provider, env=orig_env)
                    except Exception:
                        logger.error(f"Failed to rollback provider: {provider.id}")
            raise

    async def list_env(self) -> dict[str, str]:
        async with self._uow() as uow:
            return await uow.env.get_all()
