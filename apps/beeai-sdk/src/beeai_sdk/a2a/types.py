# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import uuid
from typing import Literal, TypeAlias

from a2a.types import Artifact, Message, Part, Role, TaskStatus, TextPart
from pydantic import Field, model_validator

RunYield: TypeAlias = Message | Part | TaskStatus | Artifact | str | None | dict | Exception
RunYieldResume: TypeAlias = Message | None


class ArtifactChunk(Artifact):
    last_chunk: bool = False


class AgentMessage(Message):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: Literal[Role.agent] = Role.agent  # pyright: ignore [reportIncompatibleVariableOverride]
    text: str | None = None
    parts: list[Part] | None = None

    @model_validator(mode="after")
    def text_message_validate(self):
        self.parts = self.parts or []
        if self.parts and self.text is not None:
            raise ValueError("Message cannot have both parts and text")
        if self.text is not None:
            self.parts = [Part(root=TextPart(text=self.text))]  # pyright: ignore [reportIncompatibleVariableOverride]
        return self
