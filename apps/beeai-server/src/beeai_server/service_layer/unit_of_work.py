# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Protocol, Self

from beeai_server.domain.repositories.a2a_request import IA2ARequestRepository
from beeai_server.domain.repositories.configurations import IConfigurationsRepository
from beeai_server.domain.repositories.context import IContextRepository
from beeai_server.domain.repositories.env import IEnvVariableRepository
from beeai_server.domain.repositories.file import IFileRepository
from beeai_server.domain.repositories.model_provider import IModelProviderRepository
from beeai_server.domain.repositories.provider import IProviderRepository
from beeai_server.domain.repositories.provider_build import IProviderBuildRepository
from beeai_server.domain.repositories.user import IUserRepository
from beeai_server.domain.repositories.user_feedback import IUserFeedbackRepository
from beeai_server.domain.repositories.vector_store import IVectorDatabaseRepository, IVectorStoreRepository


class IUnitOfWork(Protocol):
    providers: IProviderRepository
    provider_builds: IProviderBuildRepository
    a2a_requests: IA2ARequestRepository
    contexts: IContextRepository
    files: IFileRepository
    env: IEnvVariableRepository
    model_providers: IModelProviderRepository
    configuration: IConfigurationsRepository
    users: IUserRepository
    vector_stores: IVectorStoreRepository
    vector_database: IVectorDatabaseRepository
    user_feedback: IUserFeedbackRepository

    async def __aenter__(self) -> Self: ...
    async def __aexit__(self, exc_type, exc, tb) -> None: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...


class IUnitOfWorkFactory(Protocol):
    def __call__(self) -> IUnitOfWork: ...
