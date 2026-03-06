# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest
from a2a.types import Part, Role, TaskState, TaskStatus, TaskStatusUpdateEvent

from agentstack_sdk.a2a.types import AgentMessage, Metadata
from agentstack_sdk.server.accumulator import MessageAccumulator, MessageContext, TextPartContext

pytestmark = pytest.mark.unit


# --- State transition tests ---


class TestStateTransitions:
    def test_initial_state_is_base_level(self):
        acc = MessageAccumulator()
        assert isinstance(acc.active_context, MessageAccumulator)

    def test_string_enters_text_part_context(self):
        acc = MessageAccumulator()
        result = acc.process("hello")
        assert result.accumulated is True
        assert isinstance(acc.active_context, TextPartContext)

    def test_consecutive_strings_stay_in_text_part(self):
        acc = MessageAccumulator()
        acc.process("a")
        result = acc.process("b")
        assert result.accumulated is True
        assert isinstance(acc.active_context, TextPartContext)

    def test_part_enters_message_context(self):
        acc = MessageAccumulator()
        result = acc.process(Part(text="x"))
        assert result.accumulated is True
        assert isinstance(acc.active_context, MessageContext)

    def test_metadata_enters_message_context(self):
        acc = MessageAccumulator()
        result = acc.process(Metadata({"key": "val"}))
        assert result.accumulated is True
        assert isinstance(acc.active_context, MessageContext)

    def test_part_after_string_transitions_to_message_context(self):
        acc = MessageAccumulator()
        acc.process("text chunk")
        result = acc.process(Part(text="explicit part"))
        assert result.accumulated is True
        assert isinstance(acc.active_context, MessageContext)
        # The text chunk was built into a Part and added to the MessageContext
        ctx = acc.active_context
        assert len(ctx.parts) == 2
        assert ctx.parts[0].text == "text chunk"
        assert ctx.parts[1].text == "explicit part"

    def test_message_passthrough_at_base_level(self):
        acc = MessageAccumulator()
        msg = AgentMessage(text="hello")
        result = acc.process(msg)
        assert result.accumulated is False
        assert result.draft is None
        assert isinstance(acc.active_context, MessageAccumulator)

    def test_task_status_passthrough_at_base_level(self):
        acc = MessageAccumulator()
        status = TaskStatus(state=TaskState.TASK_STATE_WORKING)
        result = acc.process(status)
        assert result.accumulated is False
        assert result.draft is None
        assert isinstance(acc.active_context, MessageAccumulator)

    def test_task_status_update_event_passthrough_at_base_level(self):
        acc = MessageAccumulator()
        event = TaskStatusUpdateEvent(
            status=TaskStatus(state=TaskState.TASK_STATE_WORKING),
            task_id="t1",
            context_id="c1",
        )
        result = acc.process(event)
        assert result.accumulated is False
        assert isinstance(acc.active_context, MessageAccumulator)

    def test_message_flushes_accumulated_text(self):
        acc = MessageAccumulator()
        acc.process("a")
        acc.process("b")
        msg = AgentMessage(text="final")
        result = acc.process(msg)
        assert result.accumulated is False
        assert result.draft is not None
        assert result.draft.parts[0].text == "ab"
        assert isinstance(acc.active_context, MessageAccumulator)

    def test_task_status_flushes_accumulated_parts(self):
        acc = MessageAccumulator()
        acc.process(Part(text="hello"))
        status = TaskStatus(state=TaskState.TASK_STATE_WORKING)
        result = acc.process(status)
        assert result.accumulated is False
        assert result.draft is not None
        assert result.draft.parts[0].text == "hello"
        assert isinstance(acc.active_context, MessageAccumulator)

    def test_message_flushes_accumulated_text_and_parts(self):
        acc = MessageAccumulator()
        acc.process("text chunk")
        acc.process(Part(text="explicit part"))
        acc.process(Metadata({"key": "val"}))
        msg = AgentMessage(text="final")
        result = acc.process(msg)
        assert result.accumulated is False
        assert result.draft is not None
        # Draft should contain the accumulated text part and the explicit part
        assert len(result.draft.parts) == 2
        assert result.draft.parts[0].text == "text chunk"
        assert result.draft.parts[1].text == "explicit part"
        assert isinstance(acc.active_context, MessageAccumulator)

    def test_string_after_part_enters_text_part_context(self):
        acc = MessageAccumulator()
        acc.process(Part(text="first"))
        assert isinstance(acc.active_context, MessageContext)
        acc.process("streaming text")
        assert isinstance(acc.active_context, TextPartContext)

    def test_input_required_flushes_text(self):
        acc = MessageAccumulator()
        acc.process("thinking...")
        status = TaskStatus(state=TaskState.TASK_STATE_INPUT_REQUIRED)
        result = acc.process(status)
        assert result.accumulated is False
        assert result.draft is not None
        assert result.draft.parts[0].text == "thinking..."


# --- Patch verification tests ---


class TestPatchOutput:
    def test_first_string_produces_replace_root_patch(self):
        acc = MessageAccumulator()
        result = acc.process("Hello")
        assert result.patch is not None
        assert len(result.patch) == 1
        patch = result.patch[0]
        assert patch["op"] == "replace"
        assert patch["path"] == ""
        value = patch["value"]  # type: ignore[typeddict-item]
        assert value["parts"] == [{"text": "Hello"}]  # type: ignore[index]
        assert "message_id" in value  # type: ignore[operator]

    def test_subsequent_string_produces_str_ins_patch(self):
        acc = MessageAccumulator()
        acc.process("Hello")
        result = acc.process(" world")
        assert result.patch is not None
        assert len(result.patch) == 1
        patch = result.patch[0]
        assert patch["op"] == "str_ins"
        assert patch["path"] == "/parts/0/text"
        assert patch["pos"] == 5
        assert patch["value"] == " world"

    def test_str_ins_path_uses_correct_index_after_parts(self):
        acc = MessageAccumulator()
        acc.process(Part(text="first"))
        acc.process(Part(text="second"))
        acc.process("stream")  # add patch at index 2
        result = acc.process("ing")  # str_ins at index 2
        assert result.patch is not None
        assert result.patch[0]["path"] == "/parts/2/text"

    def test_first_part_produces_replace_root_patch(self):
        acc = MessageAccumulator()
        result = acc.process(Part(text="hello"))
        assert result.patch is not None
        assert len(result.patch) == 1
        patch = result.patch[0]
        assert patch["op"] == "replace"
        assert patch["path"] == ""
        value = patch["value"]
        assert value["parts"] == [{"text": "hello"}]  # type: ignore[index]
        assert "message_id" in value  # type: ignore[operator]

    def test_first_metadata_produces_replace_root_patch(self):
        acc = MessageAccumulator()
        result = acc.process(Metadata({"key": "val"}))
        assert result.patch is not None
        assert len(result.patch) == 1
        patch = result.patch[0]
        assert patch["op"] == "replace"
        assert patch["path"] == ""
        value = patch["value"]
        assert value["parts"] == []  # type: ignore[index]
        assert value["metadata"] == {"key": "val"}  # type: ignore[index]
        assert "message_id" in value  # type: ignore[operator]

    def test_second_metadata_produces_incremental_patches(self):
        acc = MessageAccumulator()
        acc.process(Metadata({"ext://test": [{"ref": "a"}]}))
        result = acc.process(Metadata({"ext://test": [{"ref": "b"}]}))
        assert result.patch is not None
        # Should produce incremental add patch, not a full replace
        assert len(result.patch) >= 1
        # The patches should target /metadata/... paths
        for op in result.patch:
            assert op["path"].startswith("/metadata/")
        # Apply all patches to verify correctness
        from agentstack_sdk.server.jsonpatch_ext import ExtendedJsonPatch
        draft = {"parts": [], "metadata": {"ext://test": [{"ref": "a"}]}}
        draft = ExtendedJsonPatch(result.patch).apply(draft)
        assert draft["metadata"]["ext://test"] == [{"ref": "a"}, {"ref": "b"}]

    def test_message_id_propagated_in_all_accumulated_results(self):
        acc = MessageAccumulator()
        r1 = acc.process("Hello")
        assert r1.message_id is not None
        r2 = acc.process(" world")
        assert r2.message_id == r1.message_id
        r3 = acc.process(Part(text="part"))
        assert r3.message_id == r1.message_id
        r4 = acc.process(Metadata({"k": "v"}))
        assert r4.message_id == r1.message_id

    def test_passthrough_has_no_patch(self):
        acc = MessageAccumulator()
        result = acc.process(AgentMessage(text="hello"))
        assert result.patch is None


# --- Flush tests ---


class TestFlush:
    def test_flush_from_text_part_returns_message(self):
        acc = MessageAccumulator()
        acc.process("hello")
        acc.process(" world")
        msg = acc.flush()
        assert msg is not None
        assert msg.role == Role.ROLE_AGENT
        assert msg.parts[0].text == "hello world"

    def test_flush_from_message_context_returns_message(self):
        acc = MessageAccumulator()
        acc.process(Part(text="a"))
        acc.process(Part(text="b"))
        msg = acc.flush()
        assert msg is not None
        assert len(msg.parts) == 2
        assert msg.parts[0].text == "a"
        assert msg.parts[1].text == "b"

    def test_flush_from_base_level_returns_none(self):
        acc = MessageAccumulator()
        assert acc.flush() is None

    def test_flush_resets_to_base_level(self):
        acc = MessageAccumulator()
        acc.process("hello")
        assert isinstance(acc.active_context, TextPartContext)
        acc.flush()
        assert isinstance(acc.active_context, MessageAccumulator)

    def test_flush_after_passthrough_returns_none(self):
        acc = MessageAccumulator()
        acc.process("hello")
        acc.process(AgentMessage(text="explicit"))  # flushes internally
        assert isinstance(acc.active_context, MessageAccumulator)
        assert acc.flush() is None

    def test_flush_with_metadata(self):
        acc = MessageAccumulator()
        acc.process(Part(text="content"))
        acc.process(Metadata({"key": "value"}))
        msg = acc.flush()
        assert msg is not None
        assert msg.parts[0].text == "content"
        from google.protobuf.json_format import MessageToDict

        assert MessageToDict(msg.metadata) == {"key": "value"}

    def test_double_flush_returns_none(self):
        acc = MessageAccumulator()
        acc.process("hello")
        msg = acc.flush()
        assert msg is not None
        assert acc.flush() is None
