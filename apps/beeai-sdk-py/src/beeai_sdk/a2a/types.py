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
    | TaskStatus  # includes InputRequired and AuthRequired (subclasses)
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


class AgentArtifact(Artifact):
    artifact_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parts: list[Part | TextPart | FilePart | DataPart]  # pyright: ignore [reportIncompatibleVariableOverride]

    @model_validator(mode="after")
    def text_message_validate(self):
        self.parts = [part if isinstance(part, Part) else Part(root=part) for part in self.parts]  # pyright: ignore [reportIncompatibleVariableOverride]
        return self


class ArtifactChunk(Artifact):
    last_chunk: bool = False
    parts: list[Part | TextPart | FilePart | DataPart]  # pyright: ignore [reportIncompatibleVariableOverride]

    @model_validator(mode="after")
    def text_message_validate(self):
        self.parts = [part if isinstance(part, Part) else Part(root=part) for part in self.parts]  # pyright: ignore [reportIncompatibleVariableOverride]
        return self


class AgentMessage(Message):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: Literal[Role.agent] = Role.agent  # pyright: ignore [reportIncompatibleVariableOverride]
    text: str | None = Field(default=None, exclude=True)
    parts: list[Part | TextPart | FilePart | DataPart] = Field(default_factory=list)

    @model_validator(mode="after")
    def text_message_validate(self):
        self.parts = [part if isinstance(part, Part) else Part(root=part) for part in self.parts]  # pyright: ignore [reportIncompatibleVariableOverride]
        if self.parts and self.text is not None:
            raise ValueError("Message cannot have both parts and text")
        if self.text is not None:
            self.parts.append(Part(root=TextPart(text=self.text)))
        return self


class InputRequired(TaskStatus):
    message: Message | None = None
    state: Literal[TaskState.input_required] = TaskState.input_required  # pyright: ignore [reportIncompatibleVariableOverride]
    text: str | None = Field(default=None, exclude=True)
    parts: list[Part | TextPart | DataPart | FilePart] = Field(exclude=True, default_factory=list)

    @model_validator(mode="after")
    def text_message_validate(self):
        self.parts = [part if isinstance(part, Part) else Part(root=part) for part in self.parts]
        if sum((self.message is not None, self.text is not None, bool(self.parts))) != 1:
            raise ValueError("At most one of message, text, or parts must be provided.")
        if self.text is not None:
            self.message = AgentMessage(text=self.text)
        elif self.parts:
            self.message = AgentMessage(parts=self.parts)
        return self


class AuthRequired(InputRequired):
    state: Literal[TaskState.auth_required] = TaskState.auth_required  # pyright: ignore [reportIncompatibleVariableOverride]
