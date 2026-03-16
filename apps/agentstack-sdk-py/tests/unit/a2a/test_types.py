# Copyright 2026 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import uuid

import pytest

from agentstack_sdk.a2a.types import (
    AgentMessage,
    Artifact,
    ArtifactChunk,
    Message,
    Part,
    Role,
    TaskState,
    TaskStatus,
    validate_message,
)

pytestmark = pytest.mark.unit


def valid_part():
    return Part(text="valid content")


def valid_message_kwargs():
    return {"message_id": str(uuid.uuid4()), "role": Role.ROLE_USER, "parts": [valid_part()]}


def test_artifact_chunk():
    artifact = ArtifactChunk(
        parts=[valid_part()],
        artifact_id=str(uuid.uuid4()),
    )
    assert artifact.metadata["_last_chunk"] is False


def test_message_validation_required_fields():
    """Test that Message raises ValueError if required fields are missing."""

    # 1. Missing message_id
    with pytest.raises(ValueError, match="message_id is required"):
        validate_message(Message(role=Role.ROLE_USER, parts=[valid_part()]))

    # 2. Missing role
    with pytest.raises(ValueError, match="role is required"):
        validate_message(Message(message_id=str(uuid.uuid4()), parts=[valid_part()]))

    # 3. Missing parts
    # 4. Empty parts (Repeated field required check)
    # TODO: enable when array length is checked
    # with pytest.raises(ValueError, match="parts is required"):
    #     validate_message(Message(message_id=str(uuid.uuid4()), role=Role.ROLE_USER))


def test_agent_message_wrapper():
    """Test AgentMessage wrapper class which provides defaults."""
    # Valid creation with text
    am = AgentMessage(text="hello")
    assert am.role == Role.ROLE_AGENT
    assert am.parts[0].text == "hello"
    assert am.message_id is not None

    # Valid creation with parts
    am2 = AgentMessage(parts=[valid_part()])
    assert am2.parts[0].text == "valid content"

    # TODO: enable when array length is checked
    # # Invalid: No content
    # with pytest.raises(ValueError, match="parts is required"):
    #     validate_message(AgentMessage())


def test_artifact_validation():
    """Test Artifact validation."""
    # Artifact requires artifact_id and parts

    # 1. Valid artifact
    _ = Artifact(artifact_id=str(uuid.uuid4()), parts=[valid_part()])

    # 2. Missing artifact_id
    with pytest.raises(ValueError, match="artifact_id is required"):
        validate_message(Artifact(parts=[valid_part()]))

    # 3. Missing parts
    # TODO: enable when array length is checked
    # # Invalid: No content
    # with pytest.raises(ValueError, match="parts is required"):
    #     validate_message(Artifact(artifact_id=str(uuid.uuid4())))


def test_task_status_validation():
    """Test TaskStatus validation."""
    # TaskStatus requires state

    # 1. Valid
    _ = TaskStatus(state=TaskState.TASK_STATE_WORKING)

    # 2. Missing state (it's an enum, default is 0 which is UNSPECIFIED)
    with pytest.raises(ValueError, match="state is required"):
        validate_message(TaskStatus())  # Should default to 0

    # Explicitly setting 0
    with pytest.raises(ValueError, match="state is required"):
        validate_message(TaskStatus(state=TaskState.TASK_STATE_UNSPECIFIED))


def test_struct_map_validation():
    """Test validation handles protobuf Struct/Map fields correctly without crashing."""
    # This specifically tests the fix for the AttributeError on Struct map fields.
    a = Artifact(
        artifact_id=str(uuid.uuid4()),
        parts=[valid_part()],
        metadata={"int_val": 1, "str_val": "test", "bool_val": True},
    )
    # Should not raise any validation errors
    validate_message(a)

    # The metadata should be accessible and correctly populated
    assert a.metadata["str_val"] == "test"
