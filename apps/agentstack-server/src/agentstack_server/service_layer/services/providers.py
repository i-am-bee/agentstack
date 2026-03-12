# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from __future__ import annotations

import logging
import uuid
from uuid import UUID

from a2a.types import AgentCard, AgentExtension
from fastapi import HTTPException
from kink import inject
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from agentstack_server.domain.constants import AGENT_DETAIL_EXTENSION_URI, SELF_REGISTRATION_EXTENSION_URI
from agentstack_server.domain.models.provider import (
    Provider,
    ProviderLocation,
    ProviderState,
    SourceType,
)
from agentstack_server.domain.models.user import User, UserRole
from agentstack_server.exceptions import ManifestLoadError
from agentstack_server.service_layer.unit_of_work import IUnitOfWorkFactory
from agentstack_server.utils.a2a import get_extension
from agentstack_server.utils.utils import utc_now

logger = logging.getLogger(__name__)


@inject
class ProviderService:
    def __init__(self, uow: IUnitOfWorkFactory):
        self._uow = uow

    async def create_provider(
        self,
        *,
        user: User,
        location: ProviderLocation,
        origin: str | None = None,
        agent_card: AgentCard | None = None,
        source_type: SourceType = SourceType.API,
    ) -> Provider:
        try:
            if not agent_card:
                agent_card = await location.load_agent_card()
            agent_card = self._inject_default_agent_detail_extension(agent_card)

            provider = Provider(
                source=location,
                origin=origin or location.origin,
                agent_card=agent_card,
                created_by=user.id,
                source_type=source_type,
            )
            if get_extension(agent_card, SELF_REGISTRATION_EXTENSION_URI):
                provider.state = ProviderState.ONLINE

        except ValueError as ex:
            raise ManifestLoadError(location=location, message=str(ex), status_code=HTTP_400_BAD_REQUEST) from ex
        except Exception as ex:
            raise ManifestLoadError(location=location, message=str(ex)) from ex

        async with self._uow() as uow:
            await uow.providers.create(provider=provider)
            await uow.commit()
        return provider

    def _inject_default_agent_detail_extension(self, agent_card: AgentCard) -> AgentCard:
        if get_extension(agent_card, AGENT_DETAIL_EXTENSION_URI):
            return agent_card

        default_extension = AgentExtension(
            uri=AGENT_DETAIL_EXTENSION_URI,
            params={"interaction_mode": "multi-turn"},
        )

        extensions = list(agent_card.capabilities.extensions or [])
        extensions.append(default_extension)
        agent_card.capabilities.extensions = extensions
        return agent_card

    async def patch_provider(
        self,
        *,
        provider_id: UUID,
        user: User,
        location: ProviderLocation | None = None,
        origin: str | None = None,
        agent_card: AgentCard | None = None,
        state: ProviderState | None = None,
    ) -> Provider:
        user_id = user.id if user.role != UserRole.ADMIN else None

        async with self._uow() as uow:
            provider = await uow.providers.get(provider_id=provider_id, user_id=user_id)

        updated_provider = provider.model_copy()
        updated_provider.source = location or updated_provider.source
        if agent_card:
            updated_provider.agent_card = self._inject_default_agent_detail_extension(agent_card)
        updated_provider.origin = origin or updated_provider.source.origin

        if state is not None:
            updated_provider.state = state
        elif agent_card and get_extension(agent_card, SELF_REGISTRATION_EXTENSION_URI):
            updated_provider.state = ProviderState.ONLINE

        if location is not None and location != provider.source:
            if not agent_card:
                try:
                    loaded_card = await location.load_agent_card()
                    updated_provider.agent_card = self._inject_default_agent_detail_extension(loaded_card)
                except ValueError as ex:
                    raise ManifestLoadError(
                        location=location, message=str(ex), status_code=HTTP_400_BAD_REQUEST
                    ) from ex
                except Exception as ex:
                    raise ManifestLoadError(location=location, message=str(ex)) from ex

        if provider == updated_provider:
            return provider

        updated_provider.updated_at = utc_now()

        async with self._uow() as uow:
            await uow.providers.update(provider=updated_provider)
            await uow.commit()

        return updated_provider

    async def preview_provider(
        self, location: ProviderLocation, agent_card: AgentCard | None = None
    ) -> Provider:
        try:
            if not agent_card:
                agent_card = await location.load_agent_card()
            agent_card = self._inject_default_agent_detail_extension(agent_card)
            provider = Provider(
                source=location,
                origin=location.origin,
                agent_card=agent_card,
                created_by=uuid.uuid4(),
            )
            return provider
        except ValueError as ex:
            raise ManifestLoadError(location=location, message=str(ex), status_code=HTTP_400_BAD_REQUEST) from ex
        except Exception as ex:
            raise ManifestLoadError(location=location, message=str(ex)) from ex

    async def delete_provider(self, *, provider_id: UUID, user: User) -> None:
        user_id = user.id if user.role != UserRole.ADMIN else None
        async with self._uow() as uow:
            await uow.providers.delete(provider_id=provider_id, user_id=user_id)
            await uow.commit()

    async def list_providers(
        self, user: User | None = None, user_owned: bool | None = None, origin: str | None = None
    ) -> list[Provider]:
        if user_owned is not None and user is None:
            raise ValueError("user_owned cannot be specified without a user")

        async with self._uow() as uow:
            providers = [
                p
                async for p in uow.providers.list(
                    user_id=user.id if user_owned is True and user else None,
                    exclude_user_id=user.id if user_owned is False and user else None,
                    origin=origin,
                )
            ]
        return providers

    async def get_provider(
        self, provider_id: UUID | None = None, location: ProviderLocation | None = None
    ) -> Provider:
        if not (bool(provider_id) ^ bool(location)):
            raise ValueError("Either provider_id or location must be provided")
        providers = [
            provider
            for provider in await self.list_providers()
            if provider.id == provider_id or provider.source == location
        ]
        if not providers:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"Provider with ID: {provider_id!s} not found")
        return providers[0]

