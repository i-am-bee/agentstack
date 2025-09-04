# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from uuid import UUID

from kink import inject

from beeai_server.domain.models.user import User, UserRole
from beeai_server.service_layer.unit_of_work import IUnitOfWorkFactory

logger = logging.getLogger(__name__)


@inject
class UserService:
    def __init__(
        self,
        uow: IUnitOfWorkFactory,
    ):
        self._uow = uow

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
