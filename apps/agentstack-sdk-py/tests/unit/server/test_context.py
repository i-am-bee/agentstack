# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest
from a2a.types import Part, Role
from google.protobuf.json_format import MessageToDict

from agentstack_sdk.a2a.types import Metadata
from agentstack_sdk.server.accumulator import MessageContext, TextPartContext

pytestmark = pytest.mark.unit


# --- TextPartContext ---


class TestTextPartContext:
    def _make(self, part_index: int = 0) -> TextPartContext:
        return TextPartContext(message_context=MessageContext(), part_index=part_index)

    def test_first_chunk_produces_replace_root_patch(self):
        ctx = self._make()
        patches = ctx.add_chunk("Hello")
        assert len(patches) == 1
        patch = patches[0]
        assert patch["op"] == "replace"
        assert patch["path"] == ""
        value = patch["value"]  # type: ignore[typeddict-item]
        assert value["parts"] == [{"text": "Hello"}]  # type: ignore[index]
        assert "message_id" in value  # type: ignore[operator]

    def test_subsequent_chunk_produces_str_ins(self):
        ctx = self._make()
        ctx.add_chunk("Hello")
        patches = ctx.add_chunk(" world")
        assert len(patches) == 1
        patch = patches[0]
        assert patch["op"] == "str_ins"
        assert patch["path"] == "/parts/0/text"
        assert patch["value"] == " world"
        assert patch["pos"] == 5

    def test_pos_advances_by_chunk_length(self):
        ctx = self._make()
        assert ctx.pos == 0
        ctx.add_chunk("abc")
        assert ctx.pos == 3
        ctx.add_chunk("de")
        assert ctx.pos == 5
        ctx.add_chunk("f")
        assert ctx.pos == 6

    def test_build_concatenates_chunks(self):
        ctx = self._make()
        ctx.add_chunk("Hello")
        ctx.add_chunk(" ")
        ctx.add_chunk("world")
        part = ctx.build()
        assert part.text == "Hello world"

    def test_str_ins_uses_part_index(self):
        ctx = self._make(part_index=3)
        ctx.add_chunk("Hello")
        patches = ctx.add_chunk(" world")
        assert patches[0]["path"] == "/parts/3/text"

    def test_build_empty_chunks(self):
        ctx = self._make()
        part = ctx.build()
        assert part.text == ""


# --- MessageContext ---


class TestMessageContext:
    def test_first_add_part_returns_replace_root_patch(self):
        ctx = MessageContext()
        patches = ctx.add_part(Part(text="hello"))
        assert len(patches) == 1
        patch = patches[0]
        assert patch["op"] == "replace"
        assert patch["path"] == ""
        value = patch["value"]  # type: ignore[typeddict-item]
        assert value["parts"] == [{"text": "hello"}]  # type: ignore[index]
        assert "message_id" in value  # type: ignore[operator]

    def test_second_add_part_returns_add_patch(self):
        ctx = MessageContext()
        ctx.add_part(Part(text="first"))
        patches = ctx.add_part(Part(text="second"))
        assert len(patches) == 1
        patch = patches[0]
        assert patch["op"] == "add"
        assert patch["path"] == "/parts/-"
        assert patch["value"]["text"] == "second"

    def test_add_part_accumulates(self):
        ctx = MessageContext()
        ctx.add_part(Part(text="a"))
        ctx.add_part(Part(text="b"))
        assert len(ctx.parts) == 2
        assert ctx.parts[0].text == "a"
        assert ctx.parts[1].text == "b"

    def test_first_add_metadata_returns_replace_root_patch(self):
        ctx = MessageContext()
        patches = ctx.add_metadata(Metadata({"key": "value"}))
        assert len(patches) == 1
        patch = patches[0]
        assert patch["op"] == "replace"
        assert patch["path"] == ""
        value = patch["value"]  # type: ignore[typeddict-item]
        assert value["parts"] == []  # type: ignore[index]
        assert value["metadata"] == {"key": "value"}  # type: ignore[index]
        assert "message_id" in value  # type: ignore[operator]

    def test_add_metadata_after_part_returns_add_patch(self):
        ctx = MessageContext()
        ctx.add_part(Part(text="hello"))
        patches = ctx.add_metadata(Metadata({"key": "value"}))
        assert len(patches) == 1
        patch = patches[0]
        assert patch["op"] == "add"
        assert patch["path"] == "/metadata"
        assert patch["value"] == {"key": "value"}

    def test_add_metadata_deep_merges(self):
        ctx = MessageContext()
        ctx.add_metadata(Metadata({"a": 1}))
        ctx.add_metadata(Metadata({"b": 2}))
        assert ctx.metadata == {"a": 1, "b": 2}

    def test_add_metadata_second_call_returns_incremental_patches(self):
        ctx = MessageContext()
        ctx.add_metadata(Metadata({"a": 1}))
        patches = ctx.add_metadata(Metadata({"b": 2}))
        assert len(patches) >= 1
        # Should produce an add for the new key, not a full replace
        assert all(op["path"].startswith("/metadata/") for op in patches)
        # Verify the patches are correct by applying them
        from agentstack_sdk.server.jsonpatch_ext import ExtendedJsonPatch
        draft = {"metadata": {"a": 1}}
        draft = ExtendedJsonPatch(patches).apply(draft)
        assert draft["metadata"] == {"a": 1, "b": 2}

    def test_add_metadata_deep_merges_nested(self):
        ctx = MessageContext()
        ctx.add_metadata(Metadata({"ext": {"x": 1}}))
        ctx.add_metadata(Metadata({"ext": {"y": 2}}))
        assert ctx.metadata == {"ext": {"x": 1, "y": 2}}

    def test_add_metadata_concatenates_arrays(self):
        """Extensions using arrays (e.g. citations, trajectory) should accumulate via concatenation."""
        uri = "https://example.com/ext/v1"
        ctx = MessageContext()
        ctx.add_metadata(Metadata({uri: [{"title": "a"}]}))
        ctx.add_metadata(Metadata({uri: [{"title": "b"}]}))
        assert ctx.metadata == {uri: [{"title": "a"}, {"title": "b"}]}

    def test_build_creates_agent_message(self):
        ctx = MessageContext()
        ctx.add_part(Part(text="hello"))
        ctx.add_metadata(Metadata({"key": "value"}))
        msg = ctx.build()
        assert msg.role == Role.ROLE_AGENT
        assert msg.message_id == str(ctx.message_id)
        assert len(msg.parts) == 1
        assert msg.parts[0].text == "hello"
        assert MessageToDict(msg.metadata) == {"key": "value"}

    def test_build_without_metadata(self):
        ctx = MessageContext()
        ctx.add_part(Part(text="hello"))
        msg = ctx.build()
        assert msg.role == Role.ROLE_AGENT
        assert len(msg.parts) == 1
        assert not MessageToDict(msg.metadata)

    def test_build_with_multiple_parts(self):
        ctx = MessageContext()
        ctx.add_part(Part(text="a"))
        ctx.add_part(Part(text="b"))
        ctx.add_part(Part(text="c"))
        msg = ctx.build()
        assert [p.text for p in msg.parts] == ["a", "b", "c"]
