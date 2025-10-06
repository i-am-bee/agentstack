# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from enum import StrEnum
from typing import Protocol, runtime_checkable
from uuid import UUID

NOT_SET = object()


class EnvStoreEntity(StrEnum):
    PROVIDER = "provider"
    MODEL_PROVIDER = "model_provider"
    USER = "user"


@runtime_checkable
class IEnvVariableRepository(Protocol):
    async def get(
        self,
        *,
        parent_entity: EnvStoreEntity,
        parent_entity_id: UUID,
        key: str,
        default: str | None = NOT_SET,  # pyright: ignore [reportArgumentType]
    ) -> str | None: ...

    async def get_all(
        self,
        parent_entity: EnvStoreEntity,
        parent_entity_ids: list[UUID],
    ) -> dict[UUID, dict[str, str]]: ...

    async def update(
        self,
        *,
        parent_entity: EnvStoreEntity,
        parent_entity_id: UUID,
        variables: dict[str, str | None] | dict[str, str],
    ) -> None: ...
