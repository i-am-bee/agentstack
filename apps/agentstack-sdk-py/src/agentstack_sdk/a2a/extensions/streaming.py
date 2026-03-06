# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from __future__ import annotations

from collections.abc import AsyncIterator
from enum import StrEnum
from types import NoneType
from typing import Any, cast

from a2a.client.client import ClientEvent
from a2a.types import (
    AgentExtension,
    Message,
    TaskArtifactUpdateEvent,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from google.protobuf.json_format import MessageToDict
from pydantic import BaseModel

from agentstack_sdk.a2a.extensions.base import (
    BaseExtensionClient,
    BaseExtensionServer,
    NoParamsBaseExtensionSpec,
)
from agentstack_sdk.a2a.types import Metadata
from agentstack_sdk.types import JsonPatch, JsonValue


class StreamingExtensionSpec(NoParamsBaseExtensionSpec[NoneType]):
    URI = "https://a2a-extensions.agentstack.beeai.dev/ui/streaming/v1"
    DESCRIPTION = "Enables fine-grained streaming of token chunks."


class StreamOperations(StrEnum):
    MESSAGE_UPDATE = "message_update"


class StreamingExtensionServer(BaseExtensionServer[StreamingExtensionSpec, NoneType]):
    """
    Adds streaming support to the A2A protocol through TaskStatusUpdateEvent.metadata object.

    Updates are emitted as metadata objects containing JSON Patch (RFC 6902) operations,
    extended with `str_ins` from json-crdt-patch for efficient text streaming.

    Supported operations:
    - replace: initialize the message draft (root replace with message_id and parts)
    - add: adding parts to the message
    - str_ins: streaming individual text chunks (=llm tokens)

    The stream is a sequential log of patches, that are applied to a final message:
    ---
    update: {..., "https://.../streaming": {"message_update": { "op": "replace", "path": "", "value": {"message_id": "...", "parts": [{"text": "Hello "}]} }, "message_id": "..."}}
    update: {..., "https://.../streaming": {"message_update": { "op": "str_ins", "path": "/parts/0/text", "pos": 6, "value": "world" }, "message_id": "..."}}
    update: {..., "https://.../streaming": {"message_update": { "op": "str_ins", "path": "/parts/0/text", "pos": 11, "value": "!" }, "message_id": "..."}}
    """

    def to_metadata(self, patches: JsonPatch, message_id: str | None = None) -> Metadata:
        payload: dict[str, Any] = {StreamOperations.MESSAGE_UPDATE: patches}
        if message_id is not None:
            payload["message_id"] = message_id
        return Metadata({self.spec.URI: cast(JsonValue, payload)})


# --- Client-side delta types ---


class TextDelta(BaseModel):
    """A text chunk appended to an existing text part."""

    part_index: int
    delta: str


class PartDelta(BaseModel):
    """A new part was added to the message."""

    part_index: int
    part: dict[str, Any]


class MetadataDelta(BaseModel):
    """Message metadata was added or updated."""

    metadata: dict[str, Any]


class ArtifactDelta(BaseModel, arbitrary_types_allowed=True):
    """An artifact update event."""

    event: TaskArtifactUpdateEvent


class StateChange(BaseModel, arbitrary_types_allowed=True):
    """A task state transition (WORKING, COMPLETED, INPUT_REQUIRED, etc.)."""

    state: int  # TaskState enum value
    message: Message | None = None


StreamDelta = TextDelta | PartDelta | MetadataDelta | ArtifactDelta | StateChange


class StreamingExtensionClient(BaseExtensionClient[StreamingExtensionSpec, NoneType]):
    """Client-side streaming consumer.

    Wraps raw A2A ``ClientEvent`` streams into a unified delta-based API.
    Works identically whether the server supports the streaming extension or not:

    - **With streaming**: patches are applied incrementally; full messages whose
      ``message_id`` was already streamed are suppressed.
    - **Without streaming**: full messages are decomposed into ``PartDelta`` /
      ``MetadataDelta`` / ``StateChange`` events so the consumer code is the same.

    Usage::

        streaming = StreamingExtensionClient(spec)
        async for delta, task in streaming.stream(client.send_message(msg)):
            match delta:
                case TextDelta(delta=text):
                    print(text, end="", flush=True)
                case PartDelta(part=part):
                    ...
                case StateChange(state=TaskState.TASK_STATE_COMPLETED):
                    print()
                case ArtifactDelta(event=evt):
                    ...
    """

    def __init__(self, spec: StreamingExtensionSpec) -> None:
        super().__init__(spec)
        self._draft: dict[str, Any] = {}
        self._message_id: str | None = None
        self._streamed_messages: dict[str, int] = {}  # message_id -> parts_count

    @property
    def draft(self) -> dict[str, Any]:
        """Current draft message built from applied patches."""
        return self._draft

    @property
    def message_id(self) -> str | None:
        """Current message_id being built from patches."""
        return self._message_id

    def to_agent_card_extensions(self, **kwargs) -> list[AgentExtension]:
        return self.spec.to_agent_card_extensions(required=False)

    async def stream(
        self,
        events: AsyncIterator[ClientEvent],
    ) -> AsyncIterator[tuple[StreamDelta, Any | None]]:
        """Consume a raw A2A event stream and yield ``(delta, task)`` pairs.

        The method handles reconciliation automatically: messages that were
        already streamed via patches are suppressed, and merged messages
        (draft + explicit) only emit the new parts beyond the streamed prefix.
        """
        async for response, task in events:
            if response.HasField("artifact_update"):
                yield ArtifactDelta(event=response.artifact_update), task
                continue

            if not response.HasField("status_update"):
                continue

            update: TaskStatusUpdateEvent = response.status_update
            patch_data = self._extract_patches(update)

            if patch_data is not None:
                # Streaming mode: apply patch and emit deltas
                for delta in self._apply_and_emit(patch_data):
                    yield delta, task
                continue

            # Non-streaming event (full message or state change)
            status: TaskStatus = update.status
            message: Message | None = status.message if status.HasField("message") else None

            if message and message.message_id and message.message_id in self._streamed_messages:
                # This message was already streamed via patches
                streamed_count = self._streamed_messages[message.message_id]
                parts_list = list(message.parts)

                if len(parts_list) > streamed_count:
                    # Merged message: emit only the new parts beyond the streamed prefix
                    for i, part in enumerate(parts_list[streamed_count:], start=streamed_count):
                        yield PartDelta(part_index=i, part=MessageToDict(part)), task

                # Emit state change with the full message for reference
                if MessageToDict(status):
                    yield StateChange(state=status.state, message=message), task

                # Clean up tracking for this message
                del self._streamed_messages[message.message_id]
                self._draft = {}
                self._message_id = None
                continue

            # Non-streamed message: decompose into deltas
            if message and message.message_id:
                for i, part in enumerate(message.parts):
                    yield PartDelta(part_index=i, part=MessageToDict(part)), task
                meta = MessageToDict(message.metadata)
                if meta:
                    yield MetadataDelta(metadata=meta), task

            if MessageToDict(status):
                yield StateChange(state=status.state, message=message), task

    def text_delta(self, event: TaskStatusUpdateEvent) -> str | None:
        """Extract text delta from streaming patch in event metadata.

        Returns the text content of the first text-producing patch, or ``None``
        if the event does not contain a text-producing streaming patch.
        """
        patches = self._extract_patches(event)
        if patches is None:
            return None
        for patch in patches:
            if (text := self._patch_text_delta(patch)) is not None:
                return text
        return None

    def apply_patch(self, event: TaskStatusUpdateEvent) -> dict[str, Any] | None:
        """Apply streaming patches to internal draft. Returns current draft state, or ``None`` if no patches."""
        patches = self._extract_patches(event)
        if patches is None:
            return None
        self._apply_patches_to_draft(patches)
        return self._draft

    def _extract_patches(self, event: TaskStatusUpdateEvent) -> list[dict[str, Any]] | None:
        """Extract the streaming patch list from event metadata, if present."""
        if not event.HasField("metadata"):
            return None
        meta = MessageToDict(event.metadata)
        if not meta or self.spec.URI not in meta:
            return None
        ext_data = meta[self.spec.URI]
        if not isinstance(ext_data, dict):
            return None
        patches = ext_data.get(StreamOperations.MESSAGE_UPDATE)
        if not isinstance(patches, list):
            return None

        # Track message_id from extension metadata
        msg_id = ext_data.get("message_id")
        if msg_id and isinstance(msg_id, str):
            self._message_id = msg_id

        return patches

    def _apply_patches_to_draft(self, patches: list[dict[str, Any]]) -> None:
        """Apply a list of patch operations to the internal draft."""
        from agentstack_sdk.server.jsonpatch_ext import ExtendedJsonPatch

        self._draft = ExtendedJsonPatch(patches).apply(self._draft)
        # Update tracking
        if self._message_id:
            parts = self._draft.get("parts", [])
            self._streamed_messages[self._message_id] = len(parts)

    def _apply_and_emit(self, patches: list[dict[str, Any]]) -> list[StreamDelta]:
        """Apply patches and return the corresponding deltas."""
        from agentstack_sdk.server.jsonpatch_ext import ExtendedJsonPatch

        deltas: list[StreamDelta] = []
        metadata_ops: list[dict[str, Any]] = []
        parts_before = len(self._draft.get("parts", []))

        self._apply_patches_to_draft(patches)

        add_parts_seen = 0
        for patch in patches:
            op = patch.get("op")
            path = patch.get("path", "")
            value = patch.get("value")

            if op == "str_ins":
                segments = path.split("/")
                if len(segments) >= 3 and segments[1] == "parts":
                    part_index = int(segments[2])
                    deltas.append(TextDelta(part_index=part_index, delta=patch.get("value", "")))

            elif op == "replace" and path == "":
                if isinstance(value, dict):
                    for i, part in enumerate(value.get("parts", [])):
                        deltas.append(PartDelta(part_index=i, part=part))
                    if meta := value.get("metadata"):
                        metadata_ops.append({"op": "replace", "path": "", "value": meta})

            elif op == "add" and path == "/parts/-":
                part_index = parts_before + add_parts_seen
                add_parts_seen += 1
                if isinstance(value, dict):
                    deltas.append(PartDelta(part_index=part_index, part=value))

            elif path.startswith("/metadata"):
                # Strip /metadata prefix and collect for incremental application
                metadata_ops.append({**patch, "path": path[len("/metadata"):]})

        if metadata_ops:
            incremental = ExtendedJsonPatch(metadata_ops).apply({})
            if incremental:
                deltas.append(MetadataDelta(metadata=incremental))

        return deltas

    @staticmethod
    def _patch_text_delta(patch: dict[str, Any]) -> str | None:
        """Extract a text delta from a single patch operation."""
        op = patch.get("op")
        value = patch.get("value")
        path = patch.get("path", "")

        if op == "str_ins":
            return value if isinstance(value, str) else None

        if op == "replace" and path == "":
            # Root replace -- extract text from first part if any
            if isinstance(value, dict):
                parts = value.get("parts", [])
                if parts and isinstance(parts[0], dict) and "text" in parts[0]:
                    return parts[0]["text"]
            return None

        if op == "add" and "/parts/" in path:
            if isinstance(value, dict) and "text" in value:
                return value["text"]
            return None

        return None
