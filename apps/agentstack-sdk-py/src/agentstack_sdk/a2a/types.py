# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import functools
import sys
import uuid
from typing import TypeAlias

from a2a.types import (
    Artifact,
    Message,
    Part,
    Role,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from google.api import field_behavior_pb2
from google.protobuf import descriptor
from google.protobuf import message as _message

from agentstack_sdk.types import JsonDict, JsonValue


class Metadata(dict[str, JsonValue]): ...


RunYield: TypeAlias = (
    Message  # includes AgentMessage (subclass)
    | Part
    | TaskStatus  # includes InputRequired and AuthRequired (subclasses)
    | Artifact
    | Metadata
    | TaskStatusUpdateEvent
    | TaskArtifactUpdateEvent
    | str
    | JsonDict
    | Exception
)
RunYieldResume: TypeAlias = Message | None


def AgentArtifact(  # noqa: N802
    parts: list[Part],
    artifact_id: str | None = None,
    name: str | None = None,
    description: str | None = None,
    metadata: Metadata | dict[str, JsonValue] | None = None,
    extensions: list[str] | None = None,
) -> Artifact:
    return Artifact(
        artifact_id=artifact_id or str(uuid.uuid4()),
        name=name,
        description=description,
        parts=parts,
        metadata=metadata,
        extensions=extensions,
    )


def ArtifactChunk(  # noqa: N802
    parts: list[Part],
    artifact_id: str,
    name: str | None = None,
    description: str | None = None,
    metadata: Metadata | dict[str, JsonValue] | None = None,
    extensions: list[str] | None = None,
    last_chunk: bool = False,
) -> Artifact:
    return Artifact(
        artifact_id=artifact_id,
        name=name,
        description=description,
        parts=parts,
        metadata={"_last_chunk": last_chunk} | (metadata or Metadata()),
        extensions=extensions,
    )


def AgentMessage(  # noqa: N802
    text: str | None = None,
    message_id: str | None = None,
    parts: list[Part] | None = None,
    metadata: Metadata | dict[str, JsonValue] | None = None,
    extensions: list[str] | None = None,
    reference_task_ids: list[str] | None = None,
    role: Role = Role.ROLE_AGENT,
    **kwargs,
) -> Message:
    if text is not None and parts is not None:
        raise ValueError("At most one of text or parts must be provided.")

    if text is not None:
        parts = [*(parts or []), Part(text=text)]
    return Message(
        message_id=message_id or str(uuid.uuid4()),
        parts=parts,
        role=role,
        metadata=metadata,
        extensions=extensions,
        reference_task_ids=reference_task_ids,
        **kwargs,
    )


def InputRequired(message: Message | None = None, text: str | None = None, **kwargs) -> TaskStatus:  # noqa: N802
    if message and text:
        raise ValueError("At most one of message or text must be provided.")
    if text is not None:
        message = AgentMessage(text=text)
    return TaskStatus(state=TaskState.TASK_STATE_INPUT_REQUIRED, message=message, **kwargs)


def AuthRequired(message: Message | None = None, text: str | None = None, **kwargs) -> TaskStatus:  # noqa: N802
    if message and text:
        raise ValueError("At most one of message or text must be provided.")
    if text is not None:
        message = AgentMessage(text=text)
    return TaskStatus(state=TaskState.TASK_STATE_AUTH_REQUIRED, message=message, **kwargs)


def validate_message(message: _message.Message):
    if problems := _validate_message(message):
        raise ValueError("Invalid message:\n" + "\n".join(problems))


def _validate_message(message: _message.Message, path: str = "") -> list[str]:
    """
    Validates that fields marked as REQUIRED in the protobuf definition are set.

    Args:
        message: The protobuf message to validate.
        path: The path to the message (used for recursive validation).

    Returns:
        A list of error strings describing missing required fields.
    """
    problems = []

    # helper to format field name with path
    def _get_path(field_name):
        return f"{path}.{field_name}" if path else field_name

    for field in message.DESCRIPTOR.fields:
        # Check if the field has the REQUIRED behavior
        options = field.GetOptions()
        if options.Extensions[field_behavior_pb2.field_behavior]:
            behaviors = options.Extensions[field_behavior_pb2.field_behavior]
            if field_behavior_pb2.FieldBehavior.REQUIRED in behaviors:
                value = getattr(message, field.name)

                # Repeated fields: Check if empty
                if field.is_repeated:
                    # TODO: This triggers validation error for empty arrays (e.g. message with no parts).
                    # Enable once streaming is refactored
                    # if not value:
                    #     problems.append(f"{_get_path(field.name)} is required but empty")
                    if field.type == descriptor.FieldDescriptor.TYPE_MESSAGE:
                        is_map = getattr(field.message_type.GetOptions(), "map_entry", False)
                        if is_map:
                            for k, v in value.items():
                                if isinstance(v, _message.Message):
                                    problems.extend(_validate_message(v, f"{_get_path(field.name)}[{k}]"))
                        else:
                            for i, item in enumerate(value):
                                problems.extend(_validate_message(item, f"{_get_path(field.name)}[{i}]"))
                    continue

                # Scalar/Message fields
                if field.type == descriptor.FieldDescriptor.TYPE_MESSAGE:
                    if not message.HasField(field.name):
                        problems.append(f"{_get_path(field.name)} is required")
                    else:
                        # Recursive validation
                        problems.extend(_validate_message(value, _get_path(field.name)))
                elif (
                    field.type == descriptor.FieldDescriptor.TYPE_STRING
                    or field.type == descriptor.FieldDescriptor.TYPE_BYTES
                ):
                    if not value:
                        problems.append(f"{_get_path(field.name)} is required")
                elif field.type == descriptor.FieldDescriptor.TYPE_ENUM and value == 0:
                    problems.append(f"{_get_path(field.name)} is required")

        else:
            # Even if the field itself isn't required, if it IS set and is a message, we should validate it recursively.
            if field.type == descriptor.FieldDescriptor.TYPE_MESSAGE:
                if field.is_repeated:
                    value = getattr(message, field.name)
                    is_map = getattr(field.message_type.GetOptions(), "map_entry", False)
                    if is_map:
                        for k, v in value.items():
                            if isinstance(v, _message.Message):
                                problems.extend(_validate_message(v, f"{_get_path(field.name)}[{k}]"))
                    else:
                        for i, item in enumerate(value):
                            problems.extend(_validate_message(item, f"{_get_path(field.name)}[{i}]"))
                elif message.HasField(field.name):
                    value = getattr(message, field.name)
                    problems.extend(_validate_message(value, _get_path(field.name)))

    return problems


def _inject_validation():
    # TODO: brainstorm options
    return

    import inspect

    import a2a.types
    from google.protobuf import message as _message

    for name, klass in inspect.getmembers(a2a.types):
        if inspect.isclass(klass) and issubclass(klass, _message.Message) and klass is not _message.Message:
            original_init = klass.__init__
            original_list_fields = klass.ListFields
            original_copy_from = klass.CopyFrom

            def _validate_in_user_scope(message):
                # TODO: is this a good idea?
                caller_module = sys._getframe(2).f_globals.get("__name__", "")
                if caller_module.startswith("a2a.") or caller_module.startswith("google."):
                    return []
                return validate_message(message)

            @functools.wraps(original_init)
            def new_init(self, *args, _name=name, _init=original_init, **kwargs):
                _init(self, *args, **kwargs)
                if errors := _validate_in_user_scope(self):
                    raise ValueError(f"Validation failed for {_name}: {', '.join(errors)}")

            @functools.wraps(original_list_fields)
            def new_list_fields(self, _name=name, _list_fields=original_list_fields):
                if errors := _validate_in_user_scope(self):
                    raise ValueError(f"Validation failed for {_name}: {', '.join(errors)}")
                return _list_fields(self)

            @functools.wraps(original_copy_from)
            def new_copy_from(self, other, _name=name, _copy_from=original_copy_from):
                if errors := _validate_in_user_scope(self):
                    raise ValueError(f"Validation failed for {_name}: {', '.join(errors)}")
                return _copy_from(self, other)

            klass.__init__ = new_init
            klass.ListFields = new_list_fields
