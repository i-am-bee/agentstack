# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from textwrap import dedent

import pydantic
from pydantic import AfterValidator, Field


def validate_metadata(metadata: dict[str, str | None]) -> dict[str, str | None]:
    if len(metadata) > 16:
        raise ValueError("Metadata must be less than 16 keys.")
    if any(len(k) > 64 for k in metadata):
        raise ValueError("Metadata keys must be less than 64 characters.")
    if any(len(v) > 512 for v in metadata.values() if v is not None):
        raise ValueError("Metadata values must be less than 512 characters.")
    return metadata


Metadata = typing.Annotated[
    dict[str, str],
    pydantic.Field(
        description=dedent(
            """
            Set of 16 key-value pairs that can be attached to an object. This can be useful for storing additional
            information about the object in a structured format, and querying for objects via API or the dashboard.

            Keys are strings with a maximum length of 64 characters. Values are strings with a maximum length of
            512 characters.
            """,
        )
    ),
    pydantic.AfterValidator(validate_metadata),
]

MetadataPatch = typing.Annotated[
    dict[str, str | None],
    Field(
        description="Metadata update, will add or overwrite existing keys, None will delete the key from metadata.",
    ),
    AfterValidator(validate_metadata),
]
