# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import yaml
from anyio import Path
from pydantic import BaseModel, FileUrl, HttpUrl, RootModel

__all__ = [
    "FileSystemModelProviderRegistryLocation",
    "ModelProviderRegistryLocation",
    "ModelProviderRegistryManifest",
    "ModelProviderRegistryRecord",
    "parse_model_providers_manifest",
]

if TYPE_CHECKING:
    # Workaround to prevent cyclic imports
    # Models from this file are used in config which is used everywhere throughout the codebase
    from agentstack_server.domain.models.model_provider import ModelProviderType


class ModelProviderRegistryRecord(BaseModel, extra="allow"):
    name: str | None = None
    description: str | None = None
    type: ModelProviderType
    base_url: HttpUrl
    api_key: str
    watsonx_project_id: str | None = None
    watsonx_space_id: str | None = None


class ModelProviderRegistryManifest(BaseModel):
    providers: list[ModelProviderRegistryRecord]


def parse_model_providers_manifest(content: dict[str, Any]) -> list[ModelProviderRegistryRecord]:
    from agentstack_server.domain.models.model_provider import ModelProviderType

    _ = ModelProviderType  # make sure this is imported

    return ModelProviderRegistryManifest.model_validate(content).providers


class FileSystemModelProviderRegistryLocation(RootModel[FileUrl]):
    root: FileUrl

    async def load(self) -> list[ModelProviderRegistryRecord]:
        if self.root.path is None:
            return []
        content = await Path(self.root.path).read_text()
        return parse_model_providers_manifest(yaml.safe_load(content))


ModelProviderRegistryLocation = FileSystemModelProviderRegistryLocation
