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

import logging

from kink import inject

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
                async for provider in uow.providers.list():
                    env_changed = env.keys() & {e.name for e in provider.env} - global_vars.keys()
                    if provider.managed and env_changed:
                        affected_providers.append(provider)
                        # Rotate managed providers which use the env (inside the transaction)
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
