# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import TypeVar

import procrastinate
from anyio import Path

import kr8s
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine

from beeai_server.jobs.procrastinate import create_app
from beeai_server.service_layer.deployment_manager import IProviderDeploymentManager
from beeai_server.configuration import Configuration, get_configuration
from beeai_server.domain.repositories.files import IObjectStorageRepository
from beeai_server.infrastructure.kubernetes.provider_deployment_manager import KubernetesProviderDeploymentManager
from beeai_server.infrastructure.object_storage.repository import S3ObjectStorageRepository

from beeai_server.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWorkFactory
from beeai_server.service_layer.unit_of_work import IUnitOfWorkFactory
from kink import di, Container

from beeai_server.utils.utils import async_to_sync_isolated

logger = logging.getLogger(__name__)


def setup_database_engine(config: Configuration) -> AsyncEngine:
    return create_async_engine(str(config.persistence.db_url.get_secret_value()), isolation_level="READ COMMITTED")


async def setup_kubernetes_client(config: Configuration):
    namespace = config.k8s_namespace
    if namespace is None:
        ns_path = Path("/var/run/secrets/kubernetes.io/serviceaccount/namespace")
        if await ns_path.exists():
            namespace = (await ns_path.read_text()).strip()

    async def api_factory():
        return await kr8s.asyncio.Api(bypass_factory=True, namespace=namespace, kubeconfig=str(config.k8s_kubeconfig))

    return api_factory


T = TypeVar("T")


async def bootstrap_dependencies(dependency_overrides: Container | None = None):
    dependency_overrides = dependency_overrides or Container()

    def _set_di(service: type[T], instance: T):
        di[service] = dependency_overrides[service] if service in dependency_overrides else instance

    di.clear_cache()
    di._aliases.clear()  # reset aliases

    _set_di(Configuration, get_configuration())
    _set_di(
        IProviderDeploymentManager,
        KubernetesProviderDeploymentManager(api_factory=await setup_kubernetes_client(di[Configuration])),
    )
    _set_di(IUnitOfWorkFactory, SqlAlchemyUnitOfWorkFactory(setup_database_engine(di[Configuration])))

    # Register object storage repository and file service
    _set_di(IObjectStorageRepository, S3ObjectStorageRepository(di[Configuration]))
    _set_di(procrastinate.App, create_app())


bootstrap_dependencies_sync = async_to_sync_isolated(bootstrap_dependencies)
