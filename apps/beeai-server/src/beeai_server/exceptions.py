# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import status
from tenacity import retry_base, retry_if_exception

if TYPE_CHECKING:
    from beeai_server.domain.models.provider import EnvVar, ProviderLocation


class PlatformError(Exception):
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR


class ManifestLoadError(PlatformError):
    location: "ProviderLocation"

    def __init__(
        self, location: "ProviderLocation", message: str | None = None, status_code: int = status.HTTP_404_NOT_FOUND
    ):
        message = message or f"Manifest at location {location} not found"
        self.status_code = status_code
        super().__init__(message)


class EntityNotFoundError(PlatformError):
    entity: str
    id: UUID | str
    attribute: str

    def __init__(
        self, entity: str, id: UUID | str, status_code: int = status.HTTP_404_NOT_FOUND, attribute: str = "id"
    ):
        self.entity = entity
        self.id = id
        self.attribute = attribute
        self.status_code = status_code
        super().__init__(f"{entity} with {attribute} {id} not found")


class InvalidVectorDimensionError(PlatformError): ...


class StorageCapacityExceededError(PlatformError):
    entity: str
    status_code: int

    def __init__(self, entity: str, max_size: int, status_code: int = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE):
        self.entity = entity
        self.status_code = status_code
        super().__init__(
            f"{entity} exceeds the limit of {max_size / 1024 / 1024:.2f} MB. "
            f"Either the {entity} is too large or you exceeded the available storage capacity."
        )


class MissingConfigurationError(Exception):
    def __init__(self, missing_env: list["EnvVar"], status_code: int = status.HTTP_400_BAD_REQUEST):
        self.missing_env = missing_env
        self.status_code = status_code


class UsageLimitExceededError(PlatformError):
    def __init__(self, message: str, status_code: int = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE):
        self.status_code = status_code
        super().__init__(message)


class DuplicateEntityError(PlatformError):
    entity: str
    field: str
    value: str | UUID | None

    def __init__(
        self,
        entity: str,
        field: str = "name",
        value: str | UUID | None = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ):
        self.entity = entity
        self.field = field
        self.value = value
        self.status_code = status_code
        message = f"Duplicate {entity} found"
        if value:
            message = f"{message}: {field}='{value}' already exists"
        super().__init__(message)


def retry_if_exception_grp_type(*exception_types: type[BaseException]) -> retry_base:
    """Handle also exception groups"""

    def _fn(exception: BaseException) -> bool:
        retry = False
        try:
            raise exception
        except* exception_types:
            retry = True
        except* BaseException:
            ...
        return retry

    return retry_if_exception(_fn)
