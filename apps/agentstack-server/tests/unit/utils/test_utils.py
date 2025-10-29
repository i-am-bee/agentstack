# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import json
from io import StringIO
from typing import Any

import pytest

from agentstack_server.utils.utils import extract_string_value_stream


def async_json_reader(obj: dict[str, Any] | str):
    stringio = StringIO(json.dumps(obj) if not isinstance(obj, str) else obj)

    async def read(size: int):
        while chunk := stringio.read(size):
            yield chunk

    return read


@pytest.mark.unit
@pytest.mark.parametrize(
    "obj",
    [
        {"text": "abcde" * 100},
        {"text": "abcde" * 100, "other_key": 42},
        {"first_key": '"text": "haha"', "text": "abcde" * 100, "other_key": 666},
        {"text": 'escape "hell\\"\\' * 1000},
        {"text": 'escape "hell2\\n\t\r\\d"\\' * 1000},
    ],
)
async def test_extract_string_value_stream(obj):
    reader = async_json_reader(obj)

    result = []
    async for chunk in extract_string_value_stream(reader, "text", chunk_size=128):
        result.append(chunk)

    assert "".join(result) == obj["text"]


@pytest.mark.unit
@pytest.mark.parametrize(
    "obj, error",
    [
        ({"txt": "aa"}, KeyError),
        ('{"text": "aaaa ', EOFError),
    ],
)
async def test_extract_string_value_stream_key_in_between_chunks(obj, error):
    reader = async_json_reader(obj)

    with pytest.raises(error):
        async for _chunk in extract_string_value_stream(reader, "text"):
            ...
