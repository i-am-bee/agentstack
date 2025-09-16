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
    message_id: str | None = None

    @computed_field
    @property
    def description(self) -> str:
        return f"- `{self.file.filename}`[{self.origin_type}]: {self.file.content_type}, {self.human_readable_size}"

    @computed_field
    @property
    def human_readable_size(self) -> str:
        size = self.file.file_size_bytes
        if size is None:
            return "unknown size"
        elif size < 1024:
            return f"{size} bytes"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"

    @computed_field
    @property
    def origin_type(self) -> OriginType:
        return ORIGIN_TYPE_BY_ROLE[self.role]
