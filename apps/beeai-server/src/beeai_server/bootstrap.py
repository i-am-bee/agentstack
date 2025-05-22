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

import asyncio
import concurrent.futures
import logging
from anyio import Path

import kr8s
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine

from beeai_server.service_layer.deployment_manager import IProviderDeploymentManager
from beeai_server.configuration import Configuration, get_configuration
from beeai_server.infrastructure.kubernetes.provider_deployment_manager import KubernetesProviderDeploymentManager

from beeai_server.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWorkFactory
from beeai_server.service_layer.unit_of_work import IUnitOfWorkFactory
from beeai_server.utils.periodic import register_all_crons
from kink import di

logger = logging.getLogger(__name__)


def setup_database_engine(config: Configuration) -> AsyncEngine:
    return create_async_engine(str(config.persistence.db_url.get_secret_value()), isolation_level="SERIALIZABLE")


async def setup_kubernetes_client(config: Configuration):
    namespace = config.k8s_namespace
    if namespace is None:
        ns_path = Path("/var/run/secrets/kubernetes.io/serviceaccount/namespace")
        if await ns_path.exists():
            namespace = (await ns_path.read_text()).strip()
    return await kr8s.asyncio.api(namespace=namespace)


async def bootstrap_dependencies():
    """
    Disclaimer:
        contains blocking calls, but it's fine because this function should run only during startup
        it is async only because it needs to call other async code
    """

    di.clear_cache()
    di._aliases.clear()  # reset aliases

    di[Configuration] = config = get_configuration()
    di[IProviderDeploymentManager] = KubernetesProviderDeploymentManager(api=await setup_kubernetes_client(config))
    di[IUnitOfWorkFactory] = SqlAlchemyUnitOfWorkFactory(setup_database_engine(config))

    register_all_crons()


def bootstrap_dependencies_sync():
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(lambda: asyncio.run(bootstrap_dependencies()))
        return future.result()
