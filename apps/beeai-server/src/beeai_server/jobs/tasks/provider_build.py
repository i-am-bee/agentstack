# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from uuid import UUID

from kink import inject
from procrastinate import Blueprint

from beeai_server.domain.models.provider import DockerImageProviderLocation
from beeai_server.domain.models.provider_build import AddProvider, BuildState, UpdateProvider
from beeai_server.jobs.queues import Queues
from beeai_server.service_layer.services.provider_build import ProviderBuildService
from beeai_server.service_layer.services.providers import ProviderService
from beeai_server.service_layer.services.users import UserService

blueprint = Blueprint()


@blueprint.task(queue=str(Queues.BUILD_PROVIDER))
@inject
async def build_provider(
    provider_build_id: str,
    provider_build_service: ProviderBuildService,
    provider_service: ProviderService,
    user_service: UserService,
):
    build = await provider_build_service.build_provider(provider_build_id=UUID(provider_build_id))
    try:
        if build.status == BuildState.BUILD_COMPLETED:
            user = await user_service.get_user(user_id=build.created_by)
            match build.on_complete:
                case UpdateProvider(provider_id=provider_id):
                    await provider_service.patch_provider(
                        provider_id=provider_id,
                        user=user,
                        location=DockerImageProviderLocation(root=build.destination),
                        origin=build.source,
                    )
                case AddProvider() as add_provider:
                    await provider_service.create_provider(
                        user=user,
                        location=DockerImageProviderLocation(root=build.destination),
                        origin=build.source,
                        auto_stop_timeout=add_provider.auto_stop_timeout,
                        variables=add_provider.variables,
                    )
        build.status = BuildState.COMPLETED
    except Exception as ex:
        build.status = BuildState.FAILED
        build.error_message = f"Failed to process {build.on_complete.type} action: {ex}"
        raise
    finally:
        await provider_build_service.update_build(provider_build=build)
