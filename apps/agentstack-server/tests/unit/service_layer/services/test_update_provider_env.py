# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from agentstack_server.domain.models.user import User, UserRole
from agentstack_server.exceptions import EntityNotFoundError

pytestmark = pytest.mark.unit


def _make_mock_uow_factory(*, get_side_effect=None, provider=None):
    """Create a mock UnitOfWork factory.

    Args:
        get_side_effect: Exception to raise when uow.providers.get() is called.
        provider: Provider object to return from uow.providers.get() (ignored if get_side_effect is set).
    """
    mock_uow = AsyncMock()

    if get_side_effect:
        mock_uow.providers.get = AsyncMock(side_effect=get_side_effect)
    else:
        mock_uow.providers.get = AsyncMock(return_value=provider)

    mock_uow.env.update = AsyncMock()
    mock_uow.env.get_all = AsyncMock(return_value={})
    mock_uow.commit = AsyncMock()

    @asynccontextmanager
    async def uow_context():
        yield mock_uow

    return uow_context


def _make_admin_user():
    return User(id=uuid4(), role=UserRole.ADMIN, email="admin@test.com")


def _make_regular_user():
    return User(id=uuid4(), role=UserRole.USER, email="user@test.com")


async def test_update_provider_env_propagates_entity_not_found():
    """Bug 2: update_provider_env must propagate EntityNotFoundError when provider_id does not exist,
    instead of silently returning None."""
    from agentstack_server.service_layer.services.providers import ProviderService

    provider_id = uuid4()
    user = _make_regular_user()

    uow_factory = _make_mock_uow_factory(
        get_side_effect=EntityNotFoundError("provider", id=str(provider_id))
    )
    deployment_manager = AsyncMock()

    service = ProviderService.__new__(ProviderService)
    service._uow = uow_factory  # type: ignore[assignment]
    service._deployment_manager = deployment_manager

    with pytest.raises(EntityNotFoundError):
        await service.update_provider_env(
            provider_id=provider_id,
            env={"KEY": "value"},
            user=user,
        )


async def test_update_provider_env_propagates_value_error_for_registry():
    """Bug 2: When provider.registry is set and allow_registry_update=False,
    the ValueError should propagate, not be swallowed."""
    from agentstack_server.service_layer.services.providers import ProviderService

    provider_id = uuid4()
    user = _make_regular_user()

    mock_provider = MagicMock()
    mock_provider.registry = MagicMock()  # truthy = has registry
    mock_provider.id = provider_id

    uow_factory = _make_mock_uow_factory(provider=mock_provider)
    # Override env.get_all to return correct structure for rollback path
    # (the except block accesses result[provider_id])
    original_factory = uow_factory

    @asynccontextmanager
    async def patched_uow_context():
        async with original_factory() as uow:
            uow.env.get_all = AsyncMock(return_value={provider_id: {}})
            yield uow

    uow_factory = patched_uow_context
    deployment_manager = AsyncMock()

    service = ProviderService.__new__(ProviderService)
    service._uow = uow_factory  # type: ignore[assignment]
    service._deployment_manager = deployment_manager

    # The ValueError from "Cannot update variables for a provider added from registry"
    # should propagate. Before the fix, provider is truthy so it enters the rollback path
    # which is correct for this case. But EntityNotFoundError (above test) was the silent one.
    with pytest.raises(ValueError, match="Cannot update variables for a provider added from registry"):
        await service.update_provider_env(
            provider_id=provider_id,
            env={"KEY": "value"},
            user=user,
            allow_registry_update=False,
        )
