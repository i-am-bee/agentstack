# Copyright 2026 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from a2a.types import Message, Part
from google.protobuf import descriptor

print("Is Message a protobuf message?", hasattr(Message, "DESCRIPTOR"))
if hasattr(Message, "DESCRIPTOR"):
    desc = Message.DESCRIPTOR
    try:
        print(f"Syntax: {desc.file.syntax}")
    except AttributeError:
        print("Syntax: Unknown")

    field = desc.fields_by_name.get("message_id")
    if field:
        # LABEL_OPTIONAL = 1, LABEL_REQUIRED = 2, LABEL_REPEATED = 3
        print(f"Field message_id label: {field.label}")
        is_required = field.label == descriptor.FieldDescriptor.LABEL_REQUIRED
        print(f"Is required? {is_required}")
    else:
        print("Field message_id not found")

    msg = Message(parts=[Part(text="hello")])
    print(f"Message initialized: {msg}")
    print(f"IsInitialized: {msg.IsInitialized()}")
    try:
        msg.SerializeToString()
        print("Serialization successful")
    except Exception as e:
        print(f"Serialization failed: {e}")
