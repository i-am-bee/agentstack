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

from typing import TYPE_CHECKING
from uuid import UUID

from starlette.status import HTTP_404_NOT_FOUND
from tenacity import retry_if_exception, retry_base

if TYPE_CHECKING:
    from beeai_server.domain.models.provider import ProviderLocation
    from beeai_server.domain.models.agent import EnvVar


class ManifestLoadError(Exception):
    location: "ProviderLocation"
    status_code: int

    def __init__(self, location: "ProviderLocation", message: str | None = None, status_code: int = HTTP_404_NOT_FOUND):
        message = message or f"Manifest at location {location} not found"
        self.status_code = status_code
        super().__init__(message)


class EntityNotFoundError(Exception):
    entity: str
    id: UUID | str

    def __init__(self, entity: str, id: UUID | str):
        self.entity = entity
        self.id = id
        super().__init__(f"{entity} with id {id} not found")


class MissingConfigurationError(Exception):
    def __init__(self, missing_env: list["EnvVar"]):
        self.missing_env = missing_env


class ProviderNotInstalledError(Exception): ...


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
