# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from uuid import UUID

from kink import inject

from beeai_server.configuration import Configuration
from beeai_server.domain.models.user import User, UserRole
from beeai_server.domain.repositories.env import EnvStoreEntity
from beeai_server.exceptions import UsageLimitExceededError
from beeai_server.service_layer.unit_of_work import IUnitOfWorkFactory

logger = logging.getLogger(__name__)


@inject
class UserService:
    def __init__(self, uow: IUnitOfWorkFactory, configuration: Configuration):
        self._uow = uow
        self._config = configuration

    async def create_user(self, *, email: str, role: UserRole = UserRole.USER) -> User:
        async with self._uow() as uow:
            user = User(email=email, role=role)
            await uow.users.create(user=user)
            await uow.commit()
            return user

    async def get_user(self, user_id: UUID) -> User:
        async with self._uow() as uow:
            return await uow.users.get(user_id=user_id)

    async def get_user_by_email(self, email: str) -> User:
        async with self._uow() as uow:
            return await uow.users.get_by_email(email=email)

    async def delete_user(self, user_id: UUID) -> None:
        async with self._uow() as uow:
            await uow.users.delete(user_id=user_id)
            await uow.commit()

    async def update_user_env(self, *, user: User, env: dict[str, str | None]):
        async with self._uow() as uow:
            if len(env) > self._config.persistence.variable_store_limit_per_users:
                raise UsageLimitExceededError("Maximum number of variables per user exceeded.")

            await uow.env.update(parent_entity=EnvStoreEntity.USER, parent_entity_id=user.id, variables=env)
            result = await uow.env.get_all(parent_entity=EnvStoreEntity.USER, parent_entity_ids=[user.id])

            if len(result) > self._config.persistence.variable_store_limit_per_users:
                raise UsageLimitExceededError("Maximum number of variables per user exceeded.")

            await uow.commit()

    async def list_user_env(self, *, user: User) -> dict[str, str]:
        async with self._uow() as uow:
            env = await uow.env.get_all(parent_entity=EnvStoreEntity.USER, parent_entity_ids=[user.id])
            return env[user.id]
