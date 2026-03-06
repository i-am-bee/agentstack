# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import difflib
import json
from collections.abc import MutableMapping, MutableSequence
from typing import Any

import jsonpatch
from jsonpatch import DiffBuilder, JsonPatch, PatchOperation


class StrInsOperation(PatchOperation):
    """
    Inserts text into a string property at a specific position.
    Operation format: { "op": "str_ins", "path": "/foo/bar", "pos": 5, "value": "text" }
    If "pos" is omitted, it defaults to appending.
    """

    def apply(self, obj: Any) -> Any:
        try:
            value = self.operation["value"]
        except KeyError:
            raise jsonpatch.InvalidJsonPatch("The operation does not contain a 'value' member")

        subobj, part = self.pointer.to_last(obj)

        if isinstance(subobj, MutableMapping):
            if part not in subobj:
                raise jsonpatch.JsonPatchConflict(f"Target path {self.location} does not exist")
            current_val = subobj[part]
        elif isinstance(subobj, MutableSequence):
            try:
                part_idx = int(part)  # type: ignore [arg-type]
                current_val = subobj[part_idx]
            except (IndexError, ValueError):
                raise jsonpatch.JsonPatchConflict(f"Target path {self.location} does not exist")
        else:
            raise jsonpatch.JsonPatchConflict(f"Cannot apply str_ins to {type(subobj)}")

        if not isinstance(current_val, str):
            raise jsonpatch.JsonPatchConflict(f"Target value at {self.location} is not a string")

        pos = self.operation.get("pos", len(current_val))
        if not isinstance(pos, (int, float)):
            raise jsonpatch.InvalidJsonPatch("The operation 'pos' member must be a number")
        pos = int(pos)

        if pos < 0 or pos > len(current_val):
            raise jsonpatch.JsonPatchConflict(
                f"Position {pos} is out of bounds for string of length {len(current_val)}"
            )

        # Insert logic: string slicing
        new_val = current_val[:pos] + value + current_val[pos:]

        if isinstance(subobj, MutableMapping):
            subobj[part] = new_val
        elif isinstance(subobj, MutableSequence):
            subobj[int(part)] = new_val  # type: ignore [arg-type]

        return obj

    def to_string(self) -> str:
        # We need to include 'pos' in the string representation
        op_dict = {"op": "str_ins", "path": self.location, "value": self.operation["value"]}
        if "pos" in self.operation:
            op_dict["pos"] = self.operation["pos"]
        return json.dumps(op_dict)


class ExtendedDiffBuilder(DiffBuilder):
    """
    Extended DiffBuilder that detects string insertions and generates `str_ins` operations.
    It uses difflib to find the most efficient string patch (currently focusing on single continuous insertion).
    """

    def _item_replaced(self, path: str, key: Any, item: Any) -> None:
        """
        Called when a value is replaced. We check if it's a string modification
        that can be represented as a str_ins operation.
        """
        # Attempt to retrieve old value using the pointer
        # path is the parent path, key is the item key/index
        # We construct the full pointer to the item
        full_path_str = path + "/" + str(key).replace("~", "~0").replace("/", "~1")
        ptr = self.pointer_cls(full_path_str)

        try:
            old_value = ptr.resolve(self.src_doc)
        except Exception:
            # Fallback to standard replace if we can't find old value (shouldn't happen)
            super()._item_replaced(path, key, item)
            return

        if isinstance(old_value, str) and isinstance(item, str):
            # Optimization: Check for simple append first (O(1)ish vs O(N))
            if item.startswith(old_value) and len(item) > len(old_value):
                diff = item[len(old_value) :]
                self.insert(
                    StrInsOperation(
                        {"op": "str_ins", "path": full_path_str, "pos": len(old_value), "value": diff},
                        pointer_cls=self.pointer_cls,
                    )
                )
                return

            # Analyze for arbitrary insertion using difflib
            # We look for exactly ONE 'insert' block and everything else 'equal'.
            # If there are deletes or replaces or multiple inserts, we fallback to full value replace
            # because str_ins only does insertion, not deletion/replacement.

            matcher = difflib.SequenceMatcher(None, old_value, item)
            opcodes = matcher.get_opcodes()

            insert_ops = [op for op in opcodes if op[0] == "insert"]
            other_ops = [op for op in opcodes if op[0] != "insert"]

            # Condition:
            # 1. Must have at least one insert (otherwise equal or delete)
            # 2. All other ops must be 'equal'
            # 3. Ideally only ONE insert op to keep patch simple (though we could support multiple)
            #    For streaming, we typically expect one chunk inserted.

            if len(insert_ops) == 1 and all(op[0] == "equal" for op in other_ops):
                tag, i1, i2, j1, j2 = insert_ops[0]
                inserted_text = item[j1:j2]

                # 'pos' is i1 (index in old string where insertion starts)

                self.insert(
                    StrInsOperation(
                        {"op": "str_ins", "path": full_path_str, "pos": i1, "value": inserted_text},
                        pointer_cls=self.pointer_cls,
                    )
                )
                return

        super()._item_replaced(path, key, item)


class ExtendedJsonPatch(JsonPatch):
    operations = dict(JsonPatch.operations)
    operations["str_ins"] = StrInsOperation  # type: ignore [assignment]


def make_patch(src: Any, dst: Any) -> ExtendedJsonPatch:
    """
    Generates a patch using the ExtendedDiffBuilder.
    """
    builder = ExtendedDiffBuilder(src, dst, jsonpatch.json.dumps, jsonpatch.JsonPointer)
    builder._compare_values("", None, src, dst)
    ops = list(builder.execute())
    # Note: jsonpatch.JsonPatch(ops) validates ops but might re-parse if passed as list of dicts?
    # Actually JsonPatch init takes list of dicts or list of PatchOperations?
    # It takes list of dicts usually. `builder.execute()` yields dicts (operation dicts).
    # Wait, `DiffBuilder.execute` yields `PatchOperation.operation` (which is a dict).
    # So `ops` is a list of dicts.
    return ExtendedJsonPatch(ops)
