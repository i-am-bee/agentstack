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
from uuid import UUID

from kink import inject

from beeai_server.domain.models.user import User
from beeai_server.service_layer.unit_of_work import IUnitOfWorkFactory

logger = logging.getLogger(__name__)


@inject
class UserService:
    def __init__(
        self,
        uow: IUnitOfWorkFactory,
    ):
        self._uow = uow

    async def create_user(self, *, email: str) -> User:
        async with self._uow() as uow:
            user = User(email=email)
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
