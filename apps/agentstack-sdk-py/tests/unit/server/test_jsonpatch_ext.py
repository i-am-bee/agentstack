# Copyright 2025 © BeeAI a Series of LF Projects, LLC

import jsonpatch
import pytest

from agentstack_sdk.server.jsonpatch_ext import StrInsOperation, make_patch


def test_str_ins_append():
    """Test optimized append detection"""
    src = {"text": "Hello"}
    dst = {"text": "Hello World"}
    patch = make_patch(src, dst)
    ops = list(patch)
    assert len(ops) == 1
    assert ops[0]["op"] == "str_ins"
    assert ops[0]["path"] == "/text"
    assert ops[0]["pos"] == 5
    assert ops[0]["value"] == " World"

    # Test apply
    assert patch.apply(src) == dst


def test_str_ins_middle():
    """Test middle insertion detection via difflib"""
    src = {"text": "Hello World"}
    dst = {"text": "Hello beautiful World"}
    patch = make_patch(src, dst)
    ops = list(patch)
    assert len(ops) == 1
    assert ops[0]["op"] == "str_ins"
    assert ops[0]["path"] == "/text"
    assert ops[0]["value"] == "beautiful "
    assert ops[0]["pos"] == 6

    assert patch.apply(src) == dst


def test_str_ins_prepend():
    """Test prepend detection"""
    src = {"text": "World"}
    dst = {"text": "Hello World"}
    patch = make_patch(src, dst)
    ops = list(patch)
    assert len(ops) == 1
    assert ops[0]["op"] == "str_ins"
    assert ops[0]["pos"] == 0
    assert ops[0]["value"] == "Hello "

    assert patch.apply(src) == dst


def test_str_ins_complex_fallback():
    """Test that multiple changes fallback to replace"""
    src = {"text": "Hello World"}
    dst = {"text": "Hi World!"}  # Changed Start and End
    patch = make_patch(src, dst)
    ops = list(patch)
    assert len(ops) == 1
    assert ops[0]["op"] == "replace"

    assert patch.apply(src) == dst


def test_str_ins_explicit_apply():
    """Test manual StrInsOperation application"""
    obj = {"foo": ["bar"]}
    op = StrInsOperation({"op": "str_ins", "path": "/foo/0", "pos": 1, "value": "az"})
    res = op.apply(obj)
    assert res["foo"][0] == "bazar"


def test_str_ins_out_of_bounds():
    obj = {"text": "foo"}
    op = StrInsOperation({"op": "str_ins", "path": "/text", "pos": 100, "value": "bar"})
    with pytest.raises(jsonpatch.JsonPatchConflict):
        op.apply(obj)
