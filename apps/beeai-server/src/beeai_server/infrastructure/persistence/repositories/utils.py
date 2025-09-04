# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from enum import StrEnum

from sqlalchemy import Enum


def sql_enum(enum: type[StrEnum], **kwargs) -> Enum:
    return Enum(enum, values_callable=lambda x: [e.value for e in x], **kwargs)
