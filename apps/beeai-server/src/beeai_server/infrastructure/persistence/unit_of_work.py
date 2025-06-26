# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from contextlib import suppress
from typing import Self

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncConnection, AsyncTransaction

from beeai_server.domain.repositories.agent import IAgentRepository
from beeai_server.domain.repositories.env import IEnvVariableRepository
from beeai_server.domain.repositories.files import IFileRepository
from beeai_server.domain.repositories.provider import IProviderRepository
from beeai_server.domain.repositories.users import IUserRepository
from beeai_server.infrastructure.persistence.repositories.files import SqlAlchemyFileRepository
from beeai_server.infrastructure.persistence.repositories.agent import SqlAlchemyAgentRepository
from beeai_server.infrastructure.persistence.repositories.env import SqlAlchemyEnvVariableRepository
from beeai_server.infrastructure.persistence.repositories.provider import SqlAlchemyProviderRepository
from beeai_server.infrastructure.persistence.repositories.users import SqlAlchemyUserRepository
from beeai_server.service_layer.unit_of_work import IUnitOfWork, IUnitOfWorkFactory


class SQLAlchemyUnitOfWork(IUnitOfWork):
    """
    One UoW == one DB transaction.
    Works purely with SQLAlchemy Core objects (insert(), update(), text(), …).
    """

    providers: IProviderRepository
    agents: IAgentRepository
    env: IEnvVariableRepository
    files: IFileRepository
    users: IUserRepository

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine: AsyncEngine = engine
        self._connection: AsyncConnection | None = None
        self._transaction: AsyncTransaction | None = None

    async def __aenter__(self) -> Self:
        if self._connection or self._transaction:
            raise RuntimeError("Unit of Work is already active. It cannot be re-entered.")
        try:
            self._connection = await self._engine.connect()
            self._transaction = await self._connection.begin()

            self.providers = SqlAlchemyProviderRepository(self._connection)
            self.agents = SqlAlchemyAgentRepository(self._connection)
            self.env = SqlAlchemyEnvVariableRepository(self._connection)
            self.files = SqlAlchemyFileRepository(self._connection)
            self.users = SqlAlchemyUserRepository(self._connection)
        except Exception as e:
            if self._connection:
                await self._connection.close()
            self._connection = None
            self._transaction = None
            raise RuntimeError(f"Failed to enter Unit of Work: {e}") from e

        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        """
        Exits the asynchronous context.

        If an exception occurred within the 'async with' block, or if
        commit/rollback was not explicitly called and the transaction is still active,
        the transaction is rolled back. The database connection is always closed.
        """

        try:
            await self.rollback()
        finally:
            with suppress(Exception):
                await self._connection.close()

    async def commit(self) -> None:
        if self._transaction and self._transaction.is_active:
            await self._transaction.commit()

    async def rollback(self) -> None:
        if self._transaction and self._transaction.is_active:
            await self._transaction.rollback()


class SqlAlchemyUnitOfWorkFactory(IUnitOfWorkFactory):
    def __init__(self, engine: AsyncEngine) -> None:
        self.engine = engine

    def __call__(self) -> SQLAlchemyUnitOfWork:
        return SQLAlchemyUnitOfWork(self.engine)
