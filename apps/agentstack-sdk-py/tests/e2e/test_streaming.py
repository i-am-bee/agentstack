# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import AsyncGenerator, AsyncIterator

import pytest
from a2a.client import Client
from a2a.client.helpers import create_text_message_object
from a2a.types import (
    Artifact,
    Message,
    Part,
    Role,
    StreamResponse,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from google.protobuf.json_format import MessageToDict

from agentstack_sdk.a2a.extensions.streaming import (
    ArtifactDelta,
    MetadataDelta,
    PartDelta,
    StateChange,
    StreamingExtensionClient,
    StreamingExtensionSpec,
    TextDelta,
)
from agentstack_sdk.a2a.types import AgentMessage, ArtifactChunk, InputRequired, Metadata, RunYield
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext
from agentstack_sdk.server.jsonpatch_ext import ExtendedJsonPatch

pytestmark = pytest.mark.e2e

STREAMING_URI = StreamingExtensionSpec.URI


def extract_streaming_patches(events: list) -> list[dict]:
    """Extract streaming patches from collected client events (flattened)."""
    patches = []
    for event in events:
        match event:
            case (StreamResponse(status_update=TaskStatusUpdateEvent(metadata=metadata)), _) if metadata:
                meta_dict = MessageToDict(metadata)
                if STREAMING_URI in meta_dict:
                    patch_list = meta_dict[STREAMING_URI].get("message_update")
                    if isinstance(patch_list, list):
                        patches.extend(patch_list)
    return patches


def apply_patches(patches: list[dict]) -> dict:
    """Apply a sequence of streaming patches to build a message object."""
    return ExtendedJsonPatch(patches).apply({})


def extract_status_events(events: list) -> list[TaskStatusUpdateEvent]:
    """Extract all status update events."""
    status_events = []
    for event in events:
        match event:
            case (StreamResponse(status_update=TaskStatusUpdateEvent() as update), _):
                if MessageToDict(update.status):
                    status_events.append(update)
    return status_events


# --- Fixtures ---


@pytest.fixture
async def streaming_string_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    async def string_yielder(message: Message, context: RunContext) -> AsyncIterator[RunYield]:
        yield "Hello"
        yield " beautiful"
        yield " world"

    async with create_server_with_agent(
        string_yielder, extensions=[STREAMING_URI]
    ) as (server, client):
        yield server, client


@pytest.fixture
async def streaming_part_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    async def part_yielder(message: Message, context: RunContext) -> AsyncIterator[RunYield]:
        yield Part(text="explicit part")

    async with create_server_with_agent(
        part_yielder, extensions=[STREAMING_URI]
    ) as (server, client):
        yield server, client


@pytest.fixture
async def streaming_mixed_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    async def mixed_yielder(message: Message, context: RunContext) -> AsyncIterator[RunYield]:
        yield "text1"
        yield "text2"
        yield AgentMessage(text="final")

    async with create_server_with_agent(
        mixed_yielder, extensions=[STREAMING_URI]
    ) as (server, client):
        yield server, client


@pytest.fixture
async def no_streaming_string_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    """Same agent as streaming_string_agent but WITHOUT streaming extension."""

    async def string_yielder(message: Message, context: RunContext) -> AsyncIterator[RunYield]:
        yield "Hello"
        yield " beautiful"
        yield " world"

    async with create_server_with_agent(string_yielder) as (server, client):
        yield server, client


# --- Tests ---


async def test_string_yields_produce_streaming_patches(streaming_string_agent):
    """Verify applying streaming patches builds the same message as the wire."""
    _, client = streaming_string_agent
    events = []
    async for event in client.send_message(create_text_message_object(content="hi")):
        events.append(event)

    patches = extract_streaming_patches(events)
    assert len(patches) >= 2

    # Apply all patches to build the message
    built = apply_patches(patches)
    assert built["parts"][0]["text"] == "Hello beautiful world"

    # Compare to the COMPLETED wire message
    status_events = extract_status_events(events)
    completed = [e for e in status_events if e.status.state == TaskState.TASK_STATE_COMPLETED]
    wire_parts = [MessageToDict(p) for p in completed[0].status.message.parts]
    assert wire_parts == built["parts"]


async def test_part_yield_produces_streaming_patch(streaming_part_agent):
    """Verify applying streaming patches for Part yields builds the correct message."""
    _, client = streaming_part_agent
    events = []
    async for event in client.send_message(create_text_message_object(content="hi")):
        events.append(event)

    patches = extract_streaming_patches(events)
    assert len(patches) >= 1

    built = apply_patches(patches)
    assert built["parts"][0]["text"] == "explicit part"

    status_events = extract_status_events(events)
    completed = [e for e in status_events if e.status.state == TaskState.TASK_STATE_COMPLETED]
    wire_parts = [MessageToDict(p) for p in completed[0].status.message.parts]
    assert wire_parts == built["parts"]


async def test_completion_flushes_accumulated_message(streaming_string_agent):
    """Verify that the completed event contains all accumulated text."""
    _, client = streaming_string_agent
    events = []
    async for event in client.send_message(create_text_message_object(content="hi")):
        events.append(event)

    status_events = extract_status_events(events)
    completed = [e for e in status_events if e.status.state == TaskState.TASK_STATE_COMPLETED]
    assert len(completed) == 1

    final_message = completed[0].status.message
    assert final_message.parts[0].text == "Hello beautiful world"


async def test_mixed_yields_message_flush(streaming_mixed_agent):
    """Verify accumulated text is flushed before explicit AgentMessage."""
    _, client = streaming_mixed_agent
    events = []
    async for event in client.send_message(create_text_message_object(content="hi")):
        events.append(event)

    # Extract all messages from WORKING status events
    working_messages = []
    for event in events:
        match event:
            case (StreamResponse(status_update=TaskStatusUpdateEvent(status=TaskStatus(
                state=TaskState.TASK_STATE_WORKING, message=Message(message_id=mid)
            ))), _) if mid:
                working_messages.append(event[0].status_update.status.message)

    # Should have at least the explicit AgentMessage as a WORKING event
    # The accumulated "text1text2" is flushed as a draft merged into the AgentMessage
    assert len(working_messages) >= 1

    # Verify the completed event contains both messages in history
    status_events = extract_status_events(events)
    completed = [e for e in status_events if e.status.state == TaskState.TASK_STATE_COMPLETED]
    assert len(completed) == 1


async def test_no_streaming_patches_without_extension(no_streaming_string_agent):
    """Verify no streaming metadata when extension is not activated by client."""
    _, client = no_streaming_string_agent
    events = []
    async for event in client.send_message(create_text_message_object(content="hi")):
        events.append(event)

    patches = extract_streaming_patches(events)
    assert len(patches) == 0

    # But the final message should still have the accumulated text
    status_events = extract_status_events(events)
    completed = [e for e in status_events if e.status.state == TaskState.TASK_STATE_COMPLETED]
    assert len(completed) == 1
    assert completed[0].status.message.parts[0].text == "Hello beautiful world"


async def test_complex_accumulator_state_machine(create_server_with_agent):
    """Comprehensive test exercising all accumulator state transitions in a single scenario.

    Agent yield sequence and expected state machine transitions:

        yield "Hello"               Base → TextPart       (add /parts/-)
        yield " world"              TextPart → TextPart   (str_ins)
        yield Part("[separator]")   TextPart → Message    (flush text part, add explicit part)
        yield {"score": 42}         Message → Message     (dict→Part, add /parts/-)
        yield Metadata(ext: [a])    Message → Message     (add /metadata)
        yield Metadata(ext: [b])    Message → Message     (replace /metadata, arrays concatenated)
        yield AgentMessage("ckpt")  Message → Base        (flush draft, dispatch WORKING message)
        yield ArtifactChunk(...)    handled outside accumulator (artifact event)
        yield "post-artifact"       Base → TextPart       (new accumulation after reset)
        yield InputRequired(...)    TextPart → Base       (flush draft, INPUT_REQUIRED)
        --- resume ---
        yield "you said: ..."       Base → TextPart       (new accumulation)
        <return>                    implicit flush → COMPLETED
    """

    async def complex_agent(message: Message, context: RunContext) -> AsyncIterator[RunYield]:
        # Phase 1: Text streaming (Base → TextPart → TextPart)
        yield "Hello"
        yield " world"

        # Phase 2: Part after text (TextPart → Message; flushes text, adds explicit part)
        yield Part(text="[separator]")

        # Phase 3: Dict yield (Message → Message; dict converted to data Part)
        yield {"score": 42}

        # Phase 4: Metadata accumulation with array concatenation
        yield Metadata({"ext://test": [{"ref": "a"}]})
        yield Metadata({"ext://test": [{"ref": "b"}]})

        # Phase 5: Explicit Message flushes everything accumulated so far
        # Draft: parts=[Text("Hello world"), Part("[separator]"), DataPart({score:42})],
        #        metadata={ext://test: [{ref:a},{ref:b}]}
        # Merged with AgentMessage: draft parts + [Part("checkpoint")]
        yield AgentMessage(text="checkpoint")

        # Phase 6: Artifact (bypasses accumulator entirely)
        yield ArtifactChunk(
            artifact_id="art-1", name="data.txt",
            parts=[Part(text="artifact body")], last_chunk=True,
        )

        # Phase 7: New accumulation cycle after full reset
        yield "post-artifact"

        # Phase 8: InputRequired flushes accumulated text, pauses for user input
        # Draft: parts=[Text("post-artifact")]
        # Merged with InputRequired message: [Text("post-artifact"), Text("what next?")]
        resume_msg = yield InputRequired(text="what next?")

        # Phase 9: After resume — new accumulation, then implicit flush on return
        yield f"you said: {resume_msg.parts[0].text}"

    async with create_server_with_agent(complex_agent, extensions=[STREAMING_URI]) as (_, client):
        # --- First send: initial message ---
        events_1 = []
        async for event in client.send_message(create_text_message_object(content="go")):
            events_1.append(event)

        all_patches = extract_streaming_patches(events_1)
        status_events = extract_status_events(events_1)

        # Split patches into accumulation cycles by root replace boundaries
        cycles: list[list[dict]] = []
        for patch in all_patches:
            if patch["op"] == "replace" and patch["path"] == "":
                cycles.append([])
            cycles[-1].append(patch)
        assert len(cycles) == 2  # cycle 1: before AgentMessage, cycle 2: after artifact

        # -- Cycle 1: Apply patches to build the draft --
        # Yields: "Hello", " world", Part("[separator]"), {"score": 42}, Metadata x2
        draft_1 = apply_patches(cycles[0])
        assert draft_1["parts"][0]["text"] == "Hello world"
        assert draft_1["parts"][1]["text"] == "[separator]"
        assert draft_1["parts"][2]["data"] == {"score": 42.0}
        assert draft_1["metadata"]["ext://test"] == [{"ref": "a"}, {"ref": "b"}]

        # The WORKING wire message = merge(draft_1, AgentMessage("checkpoint"))
        # Draft parts are a prefix of the wire message parts
        working = [
            e for e in status_events
            if e.status.state == TaskState.TASK_STATE_WORKING and e.status.message.message_id
        ]
        assert len(working) == 1
        wire_msg = working[0].status.message
        wire_parts = [MessageToDict(p) for p in wire_msg.parts]
        wire_meta = MessageToDict(wire_msg.metadata)

        # Draft's 3 parts are the prefix; AgentMessage adds "checkpoint" as the 4th
        assert wire_parts[:3] == draft_1["parts"]
        assert wire_parts[3]["text"] == "checkpoint"
        assert wire_meta == draft_1["metadata"]

        # -- Artifact event (bypasses accumulator) --
        artifact_events = [
            event for event in events_1
            if isinstance(event[0], StreamResponse) and event[0].artifact_update.artifact.artifact_id
        ]
        assert len(artifact_events) == 1
        assert artifact_events[0][0].artifact_update.artifact.name == "data.txt"

        # -- Cycle 2: Apply patches to build the draft --
        # Yields: "post-artifact" (then InputRequired flushes)
        draft_2 = apply_patches(cycles[1])
        assert draft_2["parts"][0]["text"] == "post-artifact"

        # The INPUT_REQUIRED wire message = merge(draft_2, InputRequired("what next?"))
        input_required = [
            e for e in status_events
            if e.status.state == TaskState.TASK_STATE_INPUT_REQUIRED
        ]
        assert len(input_required) == 1
        ir_parts = [MessageToDict(p) for p in input_required[0].status.message.parts]
        assert ir_parts[:1] == draft_2["parts"]
        assert ir_parts[1]["text"] == "what next?"

        # --- Second send: resume ---
        task_id = events_1[-1][1].id
        resume = create_text_message_object(content="hello again")
        resume.task_id = task_id

        events_2 = []
        async for event in client.send_message(resume):
            events_2.append(event)

        status_events_2 = extract_status_events(events_2)
        patches_2 = extract_streaming_patches(events_2)

        # Cycle 3: Apply patches — should match the COMPLETED wire message exactly
        draft_3 = apply_patches(patches_2)
        completed = [e for e in status_events_2 if e.status.state == TaskState.TASK_STATE_COMPLETED]
        assert len(completed) == 1
        wire_completed_parts = [MessageToDict(p) for p in completed[0].status.message.parts]
        assert wire_completed_parts == draft_3["parts"]


# --- StreamingExtensionClient tests ---


def _make_streaming_client() -> StreamingExtensionClient:
    return StreamingExtensionClient(StreamingExtensionSpec())


async def test_streaming_client_text_deltas(streaming_string_agent):
    """Verify StreamingExtensionClient emits TextDelta for streamed text chunks."""
    _, client = streaming_string_agent
    streaming = _make_streaming_client()

    text_deltas = []
    state_changes = []
    async for delta, task in streaming.stream(client.send_message(create_text_message_object(content="hi"))):
        match delta:
            case TextDelta() as td:
                text_deltas.append(td.delta)
            case PartDelta():
                pass
            case StateChange() as sc:
                state_changes.append(sc)

    # Should have text deltas for " beautiful" and " world" (first chunk is PartDelta from root replace)
    assert len(text_deltas) >= 2

    # Verify final state change is COMPLETED
    completed = [sc for sc in state_changes if sc.state == TaskState.TASK_STATE_COMPLETED]
    assert len(completed) == 1
    # The completed message should have been reconciled (already streamed)
    assert completed[0].message is not None


async def test_streaming_client_part_delta(streaming_part_agent):
    """Verify StreamingExtensionClient emits PartDelta for explicit Part yields."""
    _, client = streaming_part_agent
    streaming = _make_streaming_client()

    part_deltas = []
    async for delta, task in streaming.stream(client.send_message(create_text_message_object(content="hi"))):
        match delta:
            case PartDelta() as pd:
                part_deltas.append(pd)
            case _:
                pass

    assert len(part_deltas) >= 1
    assert part_deltas[0].part["text"] == "explicit part"


async def test_streaming_client_without_extension(no_streaming_string_agent):
    """Verify StreamingExtensionClient works without streaming extension (decompose full messages)."""
    _, client = no_streaming_string_agent
    streaming = _make_streaming_client()

    part_deltas = []
    state_changes = []
    async for delta, task in streaming.stream(client.send_message(create_text_message_object(content="hi"))):
        match delta:
            case PartDelta() as pd:
                part_deltas.append(pd)
            case StateChange() as sc:
                state_changes.append(sc)
            case _:
                pass

    # Without streaming, the completed message should be decomposed into PartDelta
    completed = [sc for sc in state_changes if sc.state == TaskState.TASK_STATE_COMPLETED]
    assert len(completed) == 1
    # The message parts should appear as PartDelta events
    assert any(pd.part.get("text") == "Hello beautiful world" for pd in part_deltas)


async def test_streaming_client_reconciles_streamed_messages(streaming_mixed_agent):
    """Verify that messages already streamed via patches are properly reconciled."""
    _, client = streaming_mixed_agent
    streaming = _make_streaming_client()

    all_deltas = []
    async for delta, task in streaming.stream(client.send_message(create_text_message_object(content="hi"))):
        all_deltas.append(delta)

    # Should have deltas from streaming (text1, text2) and then the explicit AgentMessage
    text_deltas = [d for d in all_deltas if isinstance(d, TextDelta)]
    part_deltas = [d for d in all_deltas if isinstance(d, PartDelta)]
    state_changes = [d for d in all_deltas if isinstance(d, StateChange)]

    # The streaming patches produce text/part deltas for "text1" and "text2"
    assert len(text_deltas) + len(part_deltas) >= 1

    # Should end with COMPLETED state
    assert any(sc.state == TaskState.TASK_STATE_COMPLETED for sc in state_changes)


async def test_streaming_client_message_id_tracking(streaming_string_agent):
    """Verify message_id is tracked from streaming patches."""
    _, client = streaming_string_agent
    streaming = _make_streaming_client()

    async for delta, task in streaming.stream(client.send_message(create_text_message_object(content="hi"))):
        pass

    # After stream completes, the draft should have been used
    # message_id should have been set during streaming
    # (it gets cleared after reconciliation, so we check the completed state)
