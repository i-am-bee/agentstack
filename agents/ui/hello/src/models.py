# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class AnyModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class TrajectoryMetadata(BaseModel):
    kind: Literal["trajectory"] = "trajectory"
    message: Optional[str] = None
    tool_name: Optional[str] = None
    tool_input: Optional[AnyModel] = None
    tool_output: Optional[AnyModel] = None


class CitationMetadata(BaseModel):
    kind: Literal["citation"] = "citation"
    start_index: Optional[int] = None
    end_index: Optional[int] = None
    url: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None


class TextPart(BaseModel):
    content: str | None = None
    metadata: Optional[CitationMetadata | TrajectoryMetadata] = Field(
        discriminator="kind", default=None
    )
