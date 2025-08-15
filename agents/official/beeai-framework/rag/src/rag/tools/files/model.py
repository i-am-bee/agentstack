# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from enum import Enum

from pydantic import AnyUrl, BaseModel


class OriginType(str, Enum):
    UPLOADED = "uploaded"
    GENERATED = "generated"


class FileChatInfo(BaseModel):
    id: str
    url: AnyUrl
    filename: str
    display_filename: str  # A sanitized version of the filename used for display, in case of naming conflicts.
    content_type: str | None = None
    file_size_bytes: int | None = None
    origin_type: OriginType