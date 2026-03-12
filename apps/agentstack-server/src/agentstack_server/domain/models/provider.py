# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import logging
from enum import StrEnum
from typing import Any
from urllib.parse import quote, urljoin
from uuid import UUID

from a2a.types import AgentCard
from a2a.utils import AGENT_CARD_WELL_KNOWN_PATH
from httpx import AsyncClient
from kink import di
from pydantic import (
    AwareDatetime,
    BaseModel,
    Field,
    HttpUrl,
    ModelWrapValidatorHandler,
    RootModel,
    model_validator,
)

from agentstack_server.configuration import Configuration
from agentstack_server.domain.constants import (
    SELF_REGISTRATION_EXTENSION_URI,
)
from agentstack_server.domain.utils import bridge_k8s_to_localhost, bridge_localhost_to_k8s
from agentstack_server.utils.a2a import get_extension
from agentstack_server.utils.utils import utc_now

logger = logging.getLogger(__name__)


class ProviderState(StrEnum):
    ONLINE = "online"
    OFFLINE = "offline"


class SourceType(StrEnum):
    KAGENTI = "kagenti"
    API = "api"


class NetworkProviderLocation(RootModel):
    root: HttpUrl

    @property
    def origin(self) -> str:
        return str(self.root)

    @property
    def a2a_url(self):
        """Clean url with no query or fragment parts"""
        assert self.root.host, "Host is required"
        return HttpUrl.build(
            scheme=self.root.scheme,
            host=self.root.host,
            port=self.root.port,
            path=self.root.path.lstrip("/") if self.root.path else None,
        )

    @model_validator(mode="wrap")
    @classmethod
    def _replace_localhost_url(cls, data: Any, handler: ModelWrapValidatorHandler):
        configuration = di[Configuration]
        url: NetworkProviderLocation = handler(data)
        if configuration.provider.self_registration_use_local_network:
            url.root = bridge_k8s_to_localhost(url.root)
        else:
            # localhost does not make sense in k8s environment, replace it with host.docker.internal for backward compatibility
            url.root = bridge_localhost_to_k8s(url.root)
        return url

    @property
    def is_on_host(self) -> bool:
        """
        Return True for self-registered providers which need to be treated a bit differently
        """
        return any(url in str(self.root) for url in {"host.docker.internal", "localhost", "127.0.0.1"})

    @property
    def provider_id(self) -> UUID:
        location_digest = hashlib.sha256(str(self.root).encode()).digest()
        return UUID(bytes=location_digest[:16])

    async def load_agent_card(self) -> AgentCard:
        from a2a.types import AgentCard

        async with AsyncClient() as client:
            try:
                response = await client.get(urljoin(str(self.a2a_url), AGENT_CARD_WELL_KNOWN_PATH), timeout=1)
                response.raise_for_status()
                card = AgentCard.model_validate(response.json())
                if ext := get_extension(card, SELF_REGISTRATION_EXTENSION_URI):
                    assert ext.params
                    self_registration_id = ext.params["self_registration_id"]
                    if quote(self.root.fragment or "", safe="") != quote(self_registration_id, safe=""):
                        raise ValueError(
                            f"Self registration id does not match: {self.root.fragment} != {self_registration_id}"
                        )
                return card
            except Exception as ex:
                raise ValueError(f"Unable to load agents from location: {self.root}: {ex}") from ex


ProviderLocation = NetworkProviderLocation


class Provider(BaseModel):
    source: ProviderLocation
    id: UUID = Field(default_factory=lambda data: data["source"].provider_id)
    source_type: SourceType = SourceType.API
    origin: str
    created_at: AwareDatetime = Field(default_factory=utc_now)
    updated_at: AwareDatetime = Field(default_factory=utc_now)
    created_by: UUID
    last_active_at: AwareDatetime = Field(default_factory=utc_now)
    agent_card: AgentCard
    state: ProviderState = ProviderState.ONLINE


class ProviderErrorMessage(BaseModel):
    message: str
