# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import json
from io import StringIO
from typing import Any

import pytest

from agentstack_server.utils.utils import (
    extract_string_value_stream,
    filter_json_recursively,
)


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


@pytest.mark.unit
def test_filter_json_recursively():
    data = {
        "a": 1,
        "b": None,
        "c": {"d": 2, "e": None, "f": {"g": 3, "h": None}},
        "i": [{"j": 4, "k": None}, {"l": None}],
    }
    assert filter_json_recursively(data) == data

    result = filter_json_recursively(data, values_to_exclude={None})
    assert result == {
        "a": 1,
        "c": {"d": 2, "f": {"g": 3}},
        "i": [{"j": 4}, {}],
    }

    # Test removing specific keys
    result_keys = filter_json_recursively(data, keys_to_exclude={"c", "k"})
    assert result_keys == {
        "a": 1,
        "b": None,
        "i": [{"j": 4}, {"l": None}],
    }

    # Test removing both
    result_both = filter_json_recursively(data, values_to_exclude={None}, keys_to_exclude={"a", "f"})
    assert result_both == {
        "c": {"d": 2},
        "i": [{"j": 4}, {}],
    }

    result_both = filter_json_recursively(
        data, values_to_exclude={None}, keys_to_exclude={"a", "f"}, exclude_empty=True
    )
    assert result_both == {"c": {"d": 2}, "i": [{"j": 4}]}

    result_both = filter_json_recursively(
        data, values_to_exclude={None}, keys_to_exclude={"a", "f", "j"}, exclude_empty=True
    )
    assert result_both == {"c": {"d": 2}}
