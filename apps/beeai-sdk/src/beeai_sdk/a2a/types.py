# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import typing
import uuid
from typing import Generic, Literal, TypeAlias

from a2a.types import (
    Artifact,
    DataPart,
    FilePart,
    FileWithBytes,
    FileWithUri,
    Message,
    Part,
    Role,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
)
from pydantic import Field, model_validator

K = typing.TypeVar("K")
V = typing.TypeVar("V")


class Metadata(dict[K, V], Generic[K, V]): ...


RunYield: TypeAlias = (
    Message  # includes AgentMessage (subclass)
    | Part
    | TaskStatus  # includes RequiresInput and RequiresAuth (subclasses)
    | Artifact
    | TextPart
    | FilePart
    | FileWithBytes
    | FileWithUri
    | Metadata
    | DataPart
    | TaskStatusUpdateEvent
    | TaskArtifactUpdateEvent
    | str
    | dict
    | Exception
)
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


msg = AgentMessage(parts=[Part(root=TextPart(text="Hello, world!"))])


class InputRequired(TaskStatus):
    message: Message | None = None
    state: Literal[TaskState.input_required] = TaskState.input_required  # pyright: ignore [reportIncompatibleVariableOverride]
    text: str | None = None

    @model_validator(mode="after")
    def text_message_validate(self):
        if self.message and self.text is not None:
            raise ValueError(" cannot have both parts and text")
        if self.text is not None:
            self.message = AgentMessage(text=self.text)
        return self


class AuthRequired(InputRequired):
    state: Literal[TaskState.auth_required] = TaskState.auth_required  # pyright: ignore [reportIncompatibleVariableOverride]
