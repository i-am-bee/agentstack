# Copyright 2026 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from a2a.types import Message, Part
from google.protobuf.json_format import MessageToDict

if __name__ == "__main__":
    msg = Message(parts=[Part(text="hello")])
    print(MessageToDict(msg))
