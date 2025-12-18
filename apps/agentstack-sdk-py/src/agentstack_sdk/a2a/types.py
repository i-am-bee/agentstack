# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import uuid
from typing import TYPE_CHECKING, Literal, TypeAlias

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

if TYPE_CHECKING:
    JsonValue: TypeAlias = list["JsonValue"] | dict[str, "JsonValue"] | str | bool | int | float | None
    JsonDict: TypeAlias = dict[str, JsonValue]
else:
    from typing import Union

    from typing_extensions import TypeAliasType

    JsonValue = TypeAliasType("JsonValue", "Union[dict[str, JsonValue], list[JsonValue], str, int, float, bool, None]")  # noqa: UP007
    JsonDict = TypeAliasType("JsonDict", "dict[str, JsonValue]")


class Metadata(dict[str, JsonValue]): ...


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
    | JsonDict
    | Exception
)
RunYieldResume: TypeAlias = Message | None


class AgentArtifact(Artifact):
    artifact_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parts: list[Part | TextPart | FilePart | DataPart]

    @model_validator(mode="after")
    def text_message_validate(self):
        self.parts = [part if isinstance(part, Part) else Part(root=part) for part in self.parts]  # pyright: ignore [reportIncompatibleVariableOverride]
        return self


class ArtifactChunk(Artifact):
    last_chunk: bool = False
    parts: list[Part | TextPart | FilePart | DataPart]

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
