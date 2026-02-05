# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import functools
import logging
import pathlib
from collections.abc import Callable

import anyio
import kr8s
import procrastinate
from kink import Container, di
from limits.aio.storage import MemoryStorage, RedisStorage, Storage
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from sqlalchemy.ext.asyncio import AsyncEngine

from agentstack_server.configuration import Configuration, get_configuration
from agentstack_server.domain.repositories.file import IObjectStorageRepository, ITextExtractionBackend
from agentstack_server.domain.repositories.openai_proxy import IOpenAIProxy
from agentstack_server.infrastructure.cache.memory_cache import MemoryCacheFactory
from agentstack_server.infrastructure.cache.redis_cache import RedisCacheFactory
from agentstack_server.infrastructure.kubernetes.provider_build_manager import KubernetesProviderBuildManager
from agentstack_server.infrastructure.kubernetes.provider_deployment_manager import KubernetesProviderDeploymentManager
from agentstack_server.infrastructure.object_storage.repository import S3ObjectStorageRepository
from agentstack_server.infrastructure.openai_proxy.openai_proxy import CustomOpenAIProxy
from agentstack_server.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWorkFactory
from agentstack_server.infrastructure.text_extraction.docling import DoclingTextExtractionBackend
from agentstack_server.jobs.procrastinate import create_app
from agentstack_server.service_layer.build_manager import IProviderBuildManager
from agentstack_server.service_layer.cache import ICacheFactory
from agentstack_server.service_layer.deployment_manager import IProviderDeploymentManager
from agentstack_server.service_layer.services.managed_mcp_service import ManagedMcpService
from agentstack_server.service_layer.unit_of_work import IUnitOfWorkFactory
from agentstack_server.utils.utils import async_to_sync_isolated

logger = logging.getLogger(__name__)


def setup_database_engine(config: Configuration) -> AsyncEngine:
    engine = config.persistence.create_async_engine(
        isolation_level="READ COMMITTED",
        hide_parameters=True,
        pool_size=20,
        max_overflow=10,
    )

    sqlalchemy_instrumentor = SQLAlchemyInstrumentor()
    if sqlalchemy_instrumentor:
        sqlalchemy_instrumentor.instrument(engine=engine.sync_engine)

    return engine


async def setup_kubernetes_client(namespace: str | None = None, kubeconfig: pathlib.Path | str | dict | None = None):
    if namespace is None:
        ns_path = anyio.Path("/var/run/secrets/kubernetes.io/serviceaccount/namespace")
        if await ns_path.exists():
            namespace = (await ns_path.read_text()).strip()

    async def api_factory():
        return await kr8s.asyncio.Api(bypass_factory=True, namespace=namespace, kubeconfig=kubeconfig)

    return api_factory


def setup_rate_limiter_storage(config: Configuration) -> Storage:
    return (
        RedisStorage("async+" + config.redis.rate_limit_db_url.get_secret_value())
        if config.redis.enabled
        else MemoryStorage()
    )


def setup_cache_factory(config: Configuration) -> ICacheFactory:
    if not config.redis.enabled:
        return MemoryCacheFactory()
    return RedisCacheFactory(config.redis.cache_db_url.get_secret_value())


async def bootstrap_dependencies(dependency_overrides: Container | None = None):
    dependency_overrides = dependency_overrides or Container()

    def _set_di[T](service: type[T], instance: T | None = None, create_instance: Callable[[], T] | None = None):
        create_instance_fn = create_instance or (lambda: instance)
        di[service] = dependency_overrides[service] if service in dependency_overrides else create_instance_fn()

    di.clear_cache()
    di._aliases.clear()  # reset aliases

    _set_di(Configuration, get_configuration())
    kr8s_api_factory = await setup_kubernetes_client(
        di[Configuration].k8s_namespace,
        di[Configuration].k8s_kubeconfig,
    )
    _set_di(
        IProviderDeploymentManager,
        KubernetesProviderDeploymentManager(
            api_factory=kr8s_api_factory,
            manifest_template_dir=di[Configuration].provider.manifest_template_dir,
        ),
    )
    _set_di(
        ManagedMcpService,
        ManagedMcpService(
            configuration=di[Configuration],
            api_factory=kr8s_api_factory,
        ),
    )
    _set_di(
        IProviderBuildManager,
        KubernetesProviderBuildManager(
            configuration=di[Configuration],
            api_factory=await setup_kubernetes_client(
                di[Configuration].provider_build.k8s_namespace,
                di[Configuration].provider_build.k8s_kubeconfig,
            ),
            manifest_template_dir=di[Configuration].provider.manifest_template_dir,
        ),
    )
    _set_di(
        IUnitOfWorkFactory,
        SqlAlchemyUnitOfWorkFactory(setup_database_engine(di[Configuration]), di[Configuration]),
    )

    # Register object storage repository and file service
    _set_di(IObjectStorageRepository, S3ObjectStorageRepository(di[Configuration]))
    _set_di(procrastinate.App, create_instance=functools.partial(create_app, di[Configuration]))
    _set_di(ITextExtractionBackend, DoclingTextExtractionBackend(di[Configuration].text_extraction))

    # Setup rate limiter storage
    _set_di(Storage, setup_rate_limiter_storage(di[Configuration]))
    _set_di(IOpenAIProxy, CustomOpenAIProxy())
    _set_di(ICacheFactory, setup_cache_factory(di[Configuration]))


bootstrap_dependencies_sync = async_to_sync_isolated(bootstrap_dependencies)
