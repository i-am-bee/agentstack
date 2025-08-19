# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from enum import StrEnum

from a2a.types import Role
from pydantic import BaseModel, computed_field

from beeai_sdk.platform import File


class OriginType(StrEnum):
    UPLOADED = "uploaded"
    GENERATED = "generated"


ORIGIN_TYPE_BY_ROLE = {
    Role.user: OriginType.UPLOADED,
    Role.agent: OriginType.GENERATED,
}


class FileChatInfo(BaseModel):
    file: File
    display_filename: str  # A sanitized version of the filename used for display, in case of naming conflicts.
    role: Role

    @computed_field
    def origin_type(self) -> OriginType:
        return ORIGIN_TYPE_BY_ROLE[self.role]
