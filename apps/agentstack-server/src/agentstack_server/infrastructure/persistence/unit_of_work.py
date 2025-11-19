# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from contextlib import AsyncExitStack, suppress
from typing import Self

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from agentstack_server.configuration import Configuration
from agentstack_server.domain.repositories.a2a_request import IA2ARequestRepository
from agentstack_server.domain.repositories.configurations import IConfigurationsRepository
from agentstack_server.domain.repositories.connector import IConnectorRepository
from agentstack_server.domain.repositories.context import IContextRepository
from agentstack_server.domain.repositories.env import IEnvVariableRepository
from agentstack_server.domain.repositories.file import IFileRepository
from agentstack_server.domain.repositories.model_provider import IModelProviderRepository
from agentstack_server.domain.repositories.provider import IProviderRepository
from agentstack_server.domain.repositories.user import IUserRepository
from agentstack_server.domain.repositories.user_feedback import IUserFeedbackRepository
from agentstack_server.domain.repositories.vector_store import IVectorDatabaseRepository, IVectorStoreRepository
from agentstack_server.infrastructure.persistence.repositories.configuration import SqlAlchemyConfigurationsRepository
from agentstack_server.infrastructure.persistence.repositories.connector import SqlAlchemyConnectorRepository
from agentstack_server.infrastructure.persistence.repositories.context import SqlAlchemyContextRepository
from agentstack_server.infrastructure.persistence.repositories.env import SqlAlchemyEnvVariableRepository
from agentstack_server.infrastructure.persistence.repositories.file import SqlAlchemyFileRepository
from agentstack_server.infrastructure.persistence.repositories.model_provider import SqlAlchemyModelProviderRepository
from agentstack_server.infrastructure.persistence.repositories.provider import SqlAlchemyProviderRepository
from agentstack_server.infrastructure.persistence.repositories.provider_build import SqlAlchemyProviderBuildRepository
from agentstack_server.infrastructure.persistence.repositories.requests import SqlAlchemyA2ARequestRepository
from agentstack_server.infrastructure.persistence.repositories.user import SqlAlchemyUserRepository
from agentstack_server.infrastructure.persistence.repositories.user_feedback import SqlAlchemyUserFeedbackRepository
from agentstack_server.infrastructure.persistence.repositories.vector_store import SqlAlchemyVectorStoreRepository
from agentstack_server.infrastructure.vector_database.vector_db import VectorDatabaseRepository
from agentstack_server.service_layer.unit_of_work import IUnitOfWork, IUnitOfWorkFactory


class SQLAlchemyUnitOfWork(IUnitOfWork):
    """
    One UoW == one DB transaction.
    Works purely with SQLAlchemy Core objects (insert(), update(), text(), …).
    """

    a2a_requests: IA2ARequestRepository
    providers: IProviderRepository
    model_providers: IModelProviderRepository
    contexts: IContextRepository
    env: IEnvVariableRepository
    files: IFileRepository
    configuration: IConfigurationsRepository
    users: IUserRepository
    vector_stores: IVectorStoreRepository
    vector_database: IVectorDatabaseRepository
    user_feedback: IUserFeedbackRepository
    connectors: IConnectorRepository

    def __init__(self, engine: AsyncEngine, config: Configuration) -> None:
        self._engine: AsyncEngine = engine
        self._connection: AsyncConnection | None = None
        self._exit_stack = AsyncExitStack()
        self._config = config

    async def __aenter__(self) -> Self:
        if self._connection:
            raise RuntimeError("Unit of Work is already active. It cannot be re-entered.")
        try:
            # No need to explicitly start transaction, we use the autobegin behavior:
            # https://docs.sqlalchemy.org/en/20/core/connections.html#commit-as-you-go
            self._connection = await self._exit_stack.enter_async_context(self._engine.connect())

            self.a2a_requests = SqlAlchemyA2ARequestRepository(self._connection)
            self.providers = SqlAlchemyProviderRepository(self._connection)
            self.model_providers = SqlAlchemyModelProviderRepository(self._connection)
            self.provider_builds = SqlAlchemyProviderBuildRepository(self._connection)
            self.contexts = SqlAlchemyContextRepository(self._connection)
            self.env = SqlAlchemyEnvVariableRepository(self._connection, configuration=self._config)
            self.files = SqlAlchemyFileRepository(self._connection)
            self.configuration = SqlAlchemyConfigurationsRepository(self._connection)
            self.users = SqlAlchemyUserRepository(self._connection)
            self.vector_stores = SqlAlchemyVectorStoreRepository(self._connection)
            self.vector_database = VectorDatabaseRepository(
                self._connection, schema_name=self._config.persistence.vector_db_schema
            )
            self.user_feedback = SqlAlchemyUserFeedbackRepository(self._connection)
            self.connectors = SqlAlchemyConnectorRepository(self._connection)

        except Exception as e:
            await self._exit_stack.aclose()
            self._connection = None
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
                await self._exit_stack.aclose()

    async def commit(self) -> None:
        if self._connection:
            await self._connection.commit()

    async def rollback(self) -> None:
        if self._connection:
            await self._connection.rollback()


class SqlAlchemyUnitOfWorkFactory(IUnitOfWorkFactory):
    def __init__(self, engine: AsyncEngine, config: Configuration) -> None:
        self.engine = engine
        self._config = config

    def __call__(self) -> SQLAlchemyUnitOfWork:
        return SQLAlchemyUnitOfWork(self.engine, config=self._config)
