# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Self

from a2a.types import (
    Message,
    Part,
    Role,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from pydantic import BaseModel, Field

from agentstack_sdk.a2a.types import Metadata, RunYield
from agentstack_sdk.types import JsonPatch, JsonPatchOp


class TextPartContext(BaseModel, arbitrary_types_allowed=True):
    chunks: list[str] = Field(default_factory=list)
    message_context: MessageContext
    part_index: int
    pos: int = 0

    def add_chunk(self, chunk: str) -> JsonPatch:
        from google.protobuf.json_format import MessageToDict

        self.chunks.append(chunk)
        part_dict = MessageToDict(Part(text=chunk))
        if self.pos == 0:
            if not self.message_context.initialized:
                self.message_context.initialized = True
                msg_id = str(self.message_context.message_id)
                patch: JsonPatchOp = {
                    "op": "replace",
                    "path": "",
                    "value": {"message_id": msg_id, "parts": [part_dict]},
                }
            else:
                patch = {"op": "add", "path": "/parts/-", "value": part_dict}
        else:
            patch = {"op": "str_ins", "pos": self.pos, "path": f"/parts/{self.part_index}/text", "value": chunk}
        self.pos += len(chunk)
        return [patch]

    def build(self) -> Part:
        return Part(text="".join(self.chunks))


class MessageContext(BaseModel, arbitrary_types_allowed=True):
    parts: list[Part] = Field(default_factory=list)
    metadata: Metadata | None = None
    initialized: bool = False
    message_id: uuid.UUID = Field(default_factory=uuid.uuid4)

    def add_metadata(self, metadata: Metadata) -> JsonPatch:
        from agentstack_sdk.server.jsonpatch_ext import make_patch
        from agentstack_sdk.server.utils import merge_metadata

        if self.metadata is None:
            self.metadata = Metadata(metadata)
            if not self.initialized:
                self.initialized = True
                return [
                    {
                        "op": "replace",
                        "path": "",
                        "value": {"message_id": str(self.message_id), "parts": [], "metadata": dict(self.metadata)},
                    }
                ]
            return [{"op": "add", "path": "/metadata", "value": dict(self.metadata)}]
        old_metadata = dict(self.metadata)
        self.metadata = merge_metadata(self.metadata, metadata)
        new_metadata = dict(self.metadata)

        ops: JsonPatch = []
        for op in make_patch(old_metadata, new_metadata).patch:
            rewritten: JsonPatchOp = {"op": op["op"], "path": f"/metadata{op['path']}"}
            if "value" in op:
                rewritten["value"] = op["value"]
            if "pos" in op:
                rewritten["pos"] = op["pos"]
            ops.append(rewritten)
        return ops

    def add_part(self, part: Part) -> JsonPatch:
        from google.protobuf.json_format import MessageToDict

        self.parts.append(part)
        part_dict = MessageToDict(part)
        if not self.initialized:
            self.initialized = True
            return [{"op": "replace", "path": "", "value": {"message_id": str(self.message_id), "parts": [part_dict]}}]
        return [{"op": "add", "path": "/parts/-", "value": part_dict}]

    def build(self) -> Message:
        m = Message(message_id=str(self.message_id), role=Role.ROLE_AGENT)
        m.parts.extend(self.parts)
        if self.metadata:
            for k, v in self.metadata.items():
                m.metadata[k] = v
        return m


@dataclass
class ProcessResult:
    """Result of processing a yield through the accumulator."""

    accumulated: bool = False
    """True if the value was consumed by the accumulator (str, Part, Metadata)."""

    draft: Message | None = None
    """Flushed message from accumulated state, when a non-accumulating yield triggers a flush."""

    patch: JsonPatch | None = None
    """Streaming patches to send as a partial update (JSON Patch operations)."""

    message_id: str | None = None
    """The message_id of the current accumulation cycle, for client-side correlation."""


class MessageAccumulator:
    """Manages the streaming accumulation state machine.

    Accumulates string chunks, Parts, and Metadata into messages,
    flushing when non-accumulating yields (Message, TaskStatus, etc.) arrive.

    The state machine has 3 levels:
    - Base level (Self): no accumulation in progress
    - MessageContext: accumulating parts and metadata into a message
    - TextPartContext: accumulating string chunks into a single text Part
    """

    def __init__(self) -> None:
        self._active: Self | MessageContext | TextPartContext = self

    @property
    def active_context(self) -> MessageAccumulator | MessageContext | TextPartContext:
        return self._active

    def process(self, value: RunYield) -> ProcessResult:
        """Process a yield value through the state machine.

        Returns a ProcessResult describing what happened:
        - accumulated=True: the value was consumed. patch may contain a streaming update.
        - accumulated=False: the value is a "control" yield (Message, TaskStatus, etc.)
          that the caller should handle. draft may contain a flushed accumulated message.
        """
        match self._active:
            case MessageAccumulator():
                return self._process_at_base_level(value)
            case MessageContext() as ctx:
                return self._process_at_message_level(ctx, value)
            case TextPartContext() as ctx:
                return self._process_at_text_part_level(ctx, value)

    def flush(self) -> Message | None:
        """Flush any accumulated state into a message. Resets to base level."""
        match self._active:
            case TextPartContext() as ctx:
                ctx.message_context.add_part(ctx.build())
                msg = ctx.message_context.build()
            case MessageContext() as ctx:
                msg = ctx.build()
            case _:
                return None
        self._active = self
        return msg

    def _process_at_base_level(self, value: RunYield) -> ProcessResult:
        match value:
            case Message() | TaskStatus() | TaskStatusUpdateEvent():
                return ProcessResult(accumulated=False)
            case _:
                self._active = MessageContext()
                return self._process_at_message_level(self._active, value)

    def _process_at_message_level(self, ctx: MessageContext, value: RunYield) -> ProcessResult:
        msg_id = str(ctx.message_id)
        match value:
            case Part() as part:
                patch = ctx.add_part(part)
                return ProcessResult(accumulated=True, patch=patch, message_id=msg_id)
            case Metadata() as metadata:
                patch = ctx.add_metadata(metadata)
                return ProcessResult(accumulated=True, patch=patch, message_id=msg_id)
            case dict() as data:
                patch = ctx.add_part(self._dict_to_part(data))
                return ProcessResult(accumulated=True, patch=patch, message_id=msg_id)
            case str():
                self._active = TextPartContext(message_context=ctx, part_index=len(ctx.parts))
                return self._process_at_text_part_level(self._active, value)
            case _:
                draft = ctx.build()
                self._active = self
                return ProcessResult(accumulated=False, draft=draft)

    @staticmethod
    def _dict_to_part(data: dict) -> Part:
        from google.protobuf.struct_pb2 import Struct, Value

        s = Struct()
        s.update(data)
        return Part(data=Value(struct_value=s))

    def _process_at_text_part_level(self, ctx: TextPartContext, value: RunYield) -> ProcessResult:
        msg_id = str(ctx.message_context.message_id)
        match value:
            case str(text):
                patch = ctx.add_chunk(text)
                return ProcessResult(accumulated=True, patch=patch, message_id=msg_id)
            case _:
                ctx.message_context.add_part(ctx.build())
                self._active = ctx.message_context
                return self._process_at_message_level(ctx.message_context, value)
