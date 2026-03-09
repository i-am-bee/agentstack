# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import ast
import enum
import functools
import json
import re
import sys
from pathlib import Path
from typing import Any
from pydantic import BaseModel, ConfigDict

import argparse

import griffe


class ExportItem(BaseModel):
    model_config = ConfigDict(validate_assignment=True)
    name: str
    origin: str
    kind: str | None = None
    docstring: str | None = None
    annotation: str | None = None
    definition: str | None = None
    default: str | None = None
    params: list[dict[str, Any]] | None = None
    returns: str | None = None
    bases: list[str] | None = None
    class_attributes: list[dict[str, Any]] | None = None
    attributes: list[dict[str, Any]] | None = None
    methods: list[dict[str, Any]] | None = None
    labels: list[str] | None = None


def parse_allnames(tree: ast.Module) -> list[str]:
    """Extract string names from a top-level __all__ = [...] assignment."""
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "__all__"
            and isinstance(node.value, ast.List)
        ):
            return [
                elt.value for elt in node.value.elts if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
            ]
    return []


def _resolve_candidate(candidate: Path) -> Path | None:
    """Resolve a candidate path to a package directory or .py module, or None."""
    if (candidate / "__init__.py").exists():
        return candidate
    if candidate.with_suffix(".py").exists():
        return candidate.with_suffix(".py")
    return None


def resolve_absolute(module_path: str, src_root: Path) -> Path | None:
    """
    Resolve an absolute dotted module path to a filesystem path, but only
    if the module lives inside the same package (src_root).
    """
    if not module_path.startswith(src_root.name):
        return None
    candidate: Path = src_root.parent
    for part in module_path.split("."):
        candidate = candidate / part
    return _resolve_candidate(candidate)


def resolve_relative(current_pkg_path: Path, level: int, module_suffix: str | None) -> Path | None:
    """
    Resolve a relative import to an absolute filesystem path.

    current_pkg_path: directory of the package containing the importing file
    level:            number of leading dots (1 = current package, 2 = parent, ...)
    module_suffix:    the `X.Y` part after the dots, or None
    Returns: Path to the resolved .py file or package directory, or None if not found.
    """
    base = current_pkg_path
    for _ in range(level - 1):
        base = base.parent

    if module_suffix:
        candidate = base
        for part in module_suffix.split("."):
            candidate = candidate / part
    else:
        candidate = base

    return _resolve_candidate(candidate)


def collect_exports(path: Path, src_root: Path, visited: set[str] | None = None) -> list[ExportItem]:
    """
    Recursively collect effective exports from a file or package directory.

    path: either a .py file or a package directory (containing __init__.py)
    Returns a deduplicated list of ExportItem(name, origin).
    """
    if visited is None:
        visited = set()

    # Normalise to the actual file we'll parse
    if path.is_dir():
        parse_file = path / "__init__.py"
        pkg_dir = path
    else:
        parse_file = path
        pkg_dir = path.parent

    str_path = str(parse_file)
    if str_path in visited:
        return []
    visited.add(str_path)

    if not parse_file.exists():
        return []

    source = parse_file.read_text()
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        print(f"  ⚠  SyntaxError in {parse_file}: {exc}", file=sys.stderr)
        return []

    exports: list[ExportItem] = []
    origin = _path_to_module(parse_file, src_root)

    # ── 1. Check for an explicit __all__ ────────────────────────────────────
    declared = parse_allnames(tree)
    if declared:
        for name in declared:
            exports.append(ExportItem(name=name, origin=origin))
        # An explicit __all__ is the final word – no need to follow star imports
        return _deduplicate(exports)

    # ── 2. No __all__: follow star imports, explicit re-exports, and local definitions ───────────
    for node in tree.body:
        # ── locally defined classes ──────────────────────────────────────────
        if isinstance(node, ast.ClassDef):
            if not node.name.startswith("_"):
                exports.append(ExportItem(name=node.name, origin=origin))
            continue

        # ── locally defined functions ────────────────────────────────────────
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                exports.append(ExportItem(name=node.name, origin=origin))
            continue

        # ── module-level assignments (constants and variables) ───────────────
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    exports.append(ExportItem(name=target.id, origin=origin))
            continue

        if isinstance(node, ast.AnnAssign):
            target = node.target
            if isinstance(target, ast.Name) and not target.id.startswith("_"):
                exports.append(ExportItem(name=target.id, origin=origin))
            continue

        if not isinstance(node, ast.ImportFrom):
            continue

        # Only handle relative imports (level > 0)
        if node.level == 0:
            # ── absolute star import from within the same package ────────────
            if node.names and node.names[0].name == "*" and node.module:
                resolved_abs = resolve_absolute(node.module, src_root)
                if resolved_abs is not None:
                    child_exports = collect_exports(resolved_abs, src_root, visited)
                    exports.extend(child_exports)
            else:
                # Capture intentional `Name as Name` re-exports
                for alias in node.names:
                    if alias.name != "*" and alias.asname == alias.name:
                        exports.append(ExportItem(name=alias.name, origin=node.module or ""))
            continue

        # ── relative wildcard: `from .X import *` ───────────────────────────
        resolved = resolve_relative(pkg_dir, node.level, node.module)
        if node.names[0].name == "*":
            if resolved is None:
                print(
                    f"  ⚠  Cannot resolve relative import {'.' * node.level}{node.module or ''} in {parse_file}",
                    file=sys.stderr,
                )
                continue
            child_exports = collect_exports(resolved, src_root, visited)
            exports.extend(child_exports)

        # ── relative explicit: `from .X import Name as Name` ────────────────
        else:
            resolved_module = _path_to_module(resolved, src_root) if resolved else (node.module or "")
            for alias in node.names:
                if alias.name != "*":
                    exports.append(ExportItem(name=alias.asname or alias.name, origin=resolved_module))

    return _deduplicate(exports)


def _path_to_module(path: Path | None, src_root: Path) -> str:
    """Convert an absolute path under src_root.parent to a dotted module name."""
    if path is None:
        return ""
    try:
        rel = path.relative_to(src_root.parent)
    except ValueError:
        return str(path)
    parts = list(rel.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    elif parts[-1].endswith(".py"):
        parts[-1] = parts[-1][:-3]
    return ".".join(parts)


def _deduplicate(exports: list[ExportItem]) -> list[ExportItem]:
    seen: set[str] = set()
    result: list[ExportItem] = []
    for exp in exports:
        if exp.name not in seen:
            seen.add(exp.name)
            result.append(exp)
    return result


@functools.lru_cache(maxsize=None)
def _init_imports_file(init_file: Path, module_stem: str) -> bool:
    """
    Return True if *init_file* contains any import that explicitly references
    a sibling module named *module_stem* (e.g. "types").

    Matches relative imports of the form:
      from .types import ...
      from . import types
    """
    if not init_file.exists():
        return False
    try:
        tree = ast.parse(init_file.read_text())
    except SyntaxError:
        return False
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.level == 0:
            continue
        # `from .types import ...`  →  node.module == "types"
        if node.module == module_stem:
            return True
        # `from . import types`  →  node.module is None, names contain "types"
        if node.module is None and any(alias.name == module_stem for alias in node.names):
            return True
    return False


# TODO: this might need to change if the logic of how the classes etc. are exposed changes
def trace_package(root: Path, src_root: Path) -> dict[str, list[ExportItem]]:
    """
    Walk every __init__.py in the package and compute its effective public API.
    Also picks up flat .py modules anywhere in the package tree that are NOT
    already referenced (imported) by the sibling __init__.py.
    It is currently not clear what should actually be exposed so this approach takes everything directly
    exposed through the __init__ files and adds everything that lies separately alongside this scheme.
    Returns {dotted_module_path: [ExportItem, ...]}.
    """
    result: dict[str, list[ExportItem]] = {}
    init_files: list[Path] = []
    other_files: list[Path] = []
    # collect and categorize all .py files under the root (skip __pycache__)
    for py_file in sorted(root.rglob("*.py")):
        if "__pycache__" in py_file.parts:
            continue
        if py_file.name == "__init__.py":
            init_files.append(py_file)
        elif not py_file.name.startswith("_"):
            other_files.append(py_file)

    # collect all the __init_.py exports, which directly define the main public API of each package
    for init_file in init_files:
        pkg_dir = init_file.parent
        module_name = _path_to_module(pkg_dir, src_root)
        exports = collect_exports(pkg_dir, src_root)  # fresh visited set per package
        result[module_name] = exports

    # Also pick up flat .py modules anywhere in the package tree (e.g. a2a/types.py).
    # Skip a file if the sibling __init__.py already imports from it — those
    # exports are already captured via the package entry above.
    for py_file in other_files:
        module_name = _path_to_module(py_file, src_root)
        if module_name in result:
            continue
        sibling_init = py_file.parent / "__init__.py"
        if _init_imports_file(sibling_init, py_file.stem):
            continue
        exports = collect_exports(py_file, src_root)
        if exports:
            result[module_name] = exports

    return result


# ── Griffe enrichment ──────────────────────────────────────────────────────


def _fmt_annotation(ann: Any) -> str | None:
    """Stringify a griffe annotation, keeping package prefixes."""
    if ann is None:
        return None
    s = str(ann)
    return s or None


def _fmt_docstring(ds: griffe.Docstring | None) -> str | None:
    if not ds or not ds.value:
        return None
    return ds.value.strip() or None


FILTER_FUNCTION_LABELS = {"module-attribute"}

_SENTINEL_DEFAULTS = frozenset({"PosOnlyArgsSep", "KwOnlyArgsSep"})
_MAX_DEFAULT_LEN = 80


def _serialize_params(fn: griffe.Function) -> list[dict[str, Any]]:
    """Serialize function/method parameters, skipping self/cls."""
    params = []
    for p in fn.parameters:
        if p.name in ("self", "cls"):
            continue
        entry: dict[str, Any] = {"name": p.name}
        if p.annotation:
            entry["type"] = _fmt_annotation(p.annotation)
        if p.default is not None and str(p.default) not in _SENTINEL_DEFAULTS:
            d = str(p.default)
            entry["default"] = d if len(d) <= _MAX_DEFAULT_LEN else d[:_MAX_DEFAULT_LEN] + "..."
        entry["kind"] = p.kind.value if p.kind and hasattr(p.kind, "value") else str(p.kind)
        params.append(entry)
    return params


def _serialize_function(fn: griffe.Function) -> dict[str, Any]:
    params = _serialize_params(fn)

    result: dict[str, Any] = {"kind": "function", "params": params}
    if fn.returns:
        result["returns"] = _fmt_annotation(fn.returns)
    doc = _fmt_docstring(fn.docstring)
    if doc:
        result["docstring"] = doc
    if fn.labels:
        result["labels"] = sorted(str(l) for l in fn.labels if str(l) not in FILTER_FUNCTION_LABELS)
    return result


def _identify_arguments_from_init(method: griffe.Function) -> list[dict[str, Any]]:
    assigns: list[dict[str, Any]] = []
    try:
        src = method.source
        if src:
            tree = ast.parse(src)
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if (
                            isinstance(target, ast.Attribute)
                            and isinstance(target.value, ast.Name)
                            and target.value.id == "self"
                            and not target.attr.startswith("_")
                        ):
                            assigns.append({"name": target.attr})
                elif isinstance(node, ast.AnnAssign):
                    if (
                        isinstance(node.target, ast.Attribute)
                        and isinstance(node.target.value, ast.Name)
                        and node.target.value.id == "self"
                        and not node.target.attr.startswith("_")
                    ):
                        entry: dict[str, Any] = {"name": node.target.attr}
                        if node.annotation:
                            entry["type"] = ast.unparse(node.annotation)
                        assigns.append(entry)
    except Exception:
        pass
    return assigns


def _is_factory_classmethod(method: griffe.Function, class_name: str) -> bool:
    """
    Return True if *method* is a @classmethod whose return annotation is
    exactly "Self" or the enclosing class name.
    """
    if "classmethod" not in {str(l) for l in method.labels}:
        return False
    ret = _fmt_annotation(method.returns)
    if not ret:
        return False

    core = ret.strip()
    # Accept bare "Self" or any qualified variant (typing.Self, typing_extensions.Self)
    # as well as the exact class name.
    return core in (class_name, "Self") or core.endswith(".Self")


def _serialize_class(cls: griffe.Class) -> dict[str, Any]:
    result: dict[str, Any] = {"kind": "class"}

    bases = [_fmt_annotation(b) for b in cls.bases if _fmt_annotation(b) not in ("object", None)]
    if bases:
        result["bases"] = bases

    doc = _fmt_docstring(cls.docstring)
    if doc:
        result["docstring"] = doc

    class_attrs: list[dict[str, Any]] = []
    methods: list[dict[str, Any]] = []
    init_assigned: list[dict[str, Any]] | None = None

    for name, member in cls.members.items():
        is_private = name.startswith("_")
        actual = member

        if isinstance(member, griffe.Alias):
            try:
                actual = member.target
            except Exception:
                continue

        kind_name = actual.kind.name

        # ── class-level attributes (excluding private and dunder) ──────────
        if kind_name == "ATTRIBUTE" and not is_private:
            field: dict[str, Any] = {"name": name}
            ann = getattr(actual, "annotation", None)
            if ann:
                field["type"] = _fmt_annotation(ann)
            field_doc = _fmt_docstring(actual.docstring)
            if field_doc:
                field["docstring"] = field_doc
            val = getattr(actual, "value", None)
            # TODO: this might need some change if we find this to be
            if val is not None:
                v = str(val)
                field["default"] = v[:120] + ("..." if len(v) > 120 else "")
            class_attrs.append(field)

        # ── public methods (excluding dunder, but including __init__) ───────
        elif kind_name == "FUNCTION" and (not is_private or name == "__init__"):
            method_info: dict[str, Any] = {"name": name}
            if name == "__init__":
                method_info["kind"] = "constructor"
                init_assigned = _identify_arguments_from_init(actual)  # pyrefly: ignore[bad-argument-type]
            elif _is_factory_classmethod(actual, cls.name):  # pyrefly: ignore[bad-argument-type]
                method_info["kind"] = "constructor"
            else:
                method_info["kind"] = "method"
            params = _serialize_params(actual)  # pyrefly: ignore[bad-argument-type]
            if params:
                method_info["params"] = params
            if hasattr(actual, "returns") and actual.returns:
                method_info["returns"] = _fmt_annotation(actual.returns)
            method_doc = _fmt_docstring(actual.docstring)
            if method_doc:
                method_info["docstring"] = method_doc
            if actual.labels:
                method_info["labels"] = sorted(str(l) for l in actual.labels)
            methods.append(method_info)

    if class_attrs:
        result["class_attributes"] = class_attrs
    if init_assigned:
        class_attrs_names = {attr["name"] for attr in class_attrs}
        result["attributes"] = [aa for aa in init_assigned if aa["name"] not in class_attrs_names]
    if methods:
        result["methods"] = methods

    return result


def _is_constant(name: str) -> bool:
    """Check if a name follows the UPPER_SNAKE_CASE constant convention."""
    return bool(re.match(r"^[A-Z0-9_]+$", name))


def _is_callable_annotation(ann_str: str | None) -> bool:
    """Return True if the annotation string represents a Callable type."""
    if not ann_str:
        return False
    return bool(re.match(r"^(typing\.)?Callable\b", ann_str))


class TypingKind(str, enum.Enum):
    SPECIAL_FORM = "special_form"
    TYPE_VAR = "type_var"
    NEW_TYPE = "new_type"
    TYPE_ALIAS = "type_alias"  # PEP 613 / PEP 695 explicit alias
    UNION_ALIAS = "union_alias"  # A | B style


_SPECIAL_FORM_PREFIXES = [
    "Literal[",
    "Union[",
    "Optional[",
    "Annotated[",
    "Final[",
    "ClassVar[",
    "Concatenate[",
]

_TYPING_KIND_PREFIXES: list[tuple[str, TypingKind]] = [
    ("TypeVar(", TypingKind.TYPE_VAR),
    ("NewType(", TypingKind.NEW_TYPE),
]

_VALUE_PREFIX_TO_KIND: list[tuple[str, TypingKind]] = [
    *(("typing." + p, TypingKind.SPECIAL_FORM) for p in _SPECIAL_FORM_PREFIXES),
    *((p, TypingKind.SPECIAL_FORM) for p in _SPECIAL_FORM_PREFIXES),
    *(("typing." + prefix, kind) for prefix, kind in _TYPING_KIND_PREFIXES),
    *_TYPING_KIND_PREFIXES,
]

_TYPE_ALIAS_ANNOTATION_NAMES = {"TypeAlias", "typing.TypeAlias", "typing_extensions.TypeAlias"}


def _is_top_level_union(val_str: str) -> bool:
    """Return True if val_str is an A | B union with at least one | outside brackets."""
    depth = 0
    for ch in val_str:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch == "|" and depth == 0:
            return True
    return False


def _get_typing_kind(attr: griffe.Attribute) -> str | None:
    """Return the TypingKind of the attribute, or None if it's not a typing construct."""
    ann = getattr(attr, "annotation", None)
    ann_str = _fmt_annotation(ann)

    # PEP 613 explicit: `Foo: TypeAlias = ...`
    if ann_str and ann_str in _TYPE_ALIAS_ANNOTATION_NAMES:
        return TypingKind.TYPE_ALIAS

    val = getattr(attr, "value", None)
    if val is None:
        return None

    val_str = str(val).strip()

    for prefix, kind in _VALUE_PREFIX_TO_KIND:
        if val_str.startswith(prefix):
            return kind

    if _is_top_level_union(val_str):
        return TypingKind.UNION_ALIAS

    return None


def _serialize_attribute(attr: griffe.Attribute, name: str = "") -> dict[str, str | list[str] | None]:
    """
    Serialize a module-level attribute/variable or constant.

    Callable-annotated attributes are serialised with kind="function".
    Type alias assignments (typing.Literal, Union, etc.) are
    serialised with kind="type_alias" and the actual type expression as "type".
    Other attributes are distinguished as constants (UPPER_SNAKE_CASE) or
    regular variables.
    """
    ann = getattr(attr, "annotation", None)
    ann_str = _fmt_annotation(ann)
    result: dict[str, str | list[str] | None] = {}
    doc = _fmt_docstring(attr.docstring)
    if doc:
        result["docstring"] = doc

    if typing_kind := _get_typing_kind(attr):
        val = getattr(attr, "value", None)
        type_str = str(val).strip() if val is not None else ann_str
        result["kind"] = typing_kind
        if type_str:
            result["definition"] = type_str

        return result

    if ann:
        result["annotation"] = ann_str

    if _is_callable_annotation(ann_str):
        result["kind"] = "function"
        if attr.labels:
            result["labels"] = sorted(str(l) for l in attr.labels if str(l) not in FILTER_FUNCTION_LABELS)
        return result

    kind = "constant" if _is_constant(name) else "attribute"
    result["kind"] = kind
    val = getattr(attr, "value", None)
    if val is not None:
        v = str(val)
        if len(v) <= 200:
            result["value"] = v

    return result


def _lookup_griffe(pkg: griffe.Module, dotted_path: str, name: str) -> griffe.Object | None:
    """Resolve dotted_path in the griffe module tree, then look up name."""
    try:
        obj = pkg
        relative = dotted_path.removeprefix(f"{pkg.name}.")
        if relative and relative != pkg.name:
            for part in relative.split("."):
                obj = obj[part]
        return obj[name]
    except (KeyError, TypeError):
        return None


_UNWANTED_ANNOTATIONS = {
    "logging.Logger",
    "Logger",
    "logging.RootLogger",
    "RootLogger",
    "TypeVar",
    "typing.TypeVar",
}

_UNWANTED_VALUE_PREFIXES = {
    "logging.getLogger",
    "getLogger",
    "TypeVar",
    "typing.TypeVar",
}


def _is_unwanted_attribute(attr: griffe.Attribute) -> bool:
    """Return True if the attribute is a logging.Logger instance or TypeVar."""
    ann = getattr(attr, "annotation", None)
    if _fmt_annotation(ann) in _UNWANTED_ANNOTATIONS:
        return True

    val = getattr(attr, "value", None)
    if val is not None:
        val_str = str(val).strip()
        return any(val_str.startswith(f"{prefix}(") for prefix in _UNWANTED_VALUE_PREFIXES)

    return False


def enrich_api(
    api: dict[str, list[ExportItem]],
    pkg: griffe.Module,
) -> dict[str, list[dict[str, Any]]]:
    """
    For every ExportItem in *api*, look up the object in the griffe tree and
    attach rich metadata.  Returns a JSON-serialisable dict.
    """
    result: dict[str, list[dict[str, Any]]] = {}

    for module_path, exports in sorted(api.items()):
        if not exports:
            continue
        enriched_exports = []
        for exp in exports:
            member = _lookup_griffe(pkg, exp.origin, exp.name)

            # Resolve through aliases
            if member is not None and member.kind.name == "ALIAS":
                if hasattr(member, "target"):
                    member = member.target
                else:
                    member = None

            if member is None:
                exp.kind = "unknown"
                enriched_exports.append(exp.model_dump(exclude_none=True))
                continue

            kind = member.kind.name
            if kind == "CLASS":
                exp = exp.model_copy(update=_serialize_class(member))  # pyrefly: ignore[bad-argument-type]
            elif kind == "FUNCTION":
                exp = exp.model_copy(update=_serialize_function(member))  # pyrefly: ignore[bad-argument-type]
            elif kind == "ATTRIBUTE":
                if _is_unwanted_attribute(member):  # pyrefly: ignore[bad-argument-type]
                    continue
                exp = exp.model_copy(
                    update=_serialize_attribute(member, exp.name)
                )  # pyrefly: ignore[bad-argument-type]
            else:
                exp.kind = kind.lower()
                doc = _fmt_docstring(getattr(member, "docstring", None))
                if doc:
                    exp.docstring = doc

            enriched_exports.append(exp.model_dump(exclude_none=True))
        result[module_path] = enriched_exports

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Introspect agentstack-sdk-py exports and emit a JSON manifest.")
    parser.add_argument(
        "--src-root",
        type=Path,
        help="Path to the agentstack_sdk package source directory",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path(__file__).resolve().parent / "exports_structure.json",
        help="Path where the JSON manifest will be written (default: <script-dir>/exports_structure.json)",
    )
    args = parser.parse_args()

    # Allow helper functions (resolve_absolute, _path_to_module) to use the
    # correct source root when --src-root is overridden.
    src_root = Path(args.src_root.resolve())

    if not src_root.exists():
        sys.exit(f"Package source not found at {src_root}")

    # ── Phase 1: star-import tracing ─────────────────────────────────────────
    api = trace_package(src_root, src_root)

    # ── Phase 2: griffe enrichment ───────────────────────────────────────────
    pkg = griffe.load(src_root.name, search_paths=[str(src_root.parent)])
    enriched = enrich_api(api, pkg)

    out_file: Path = args.output
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(enriched, indent=2))

    pkg_count = len(enriched)
    name_count = sum(len(v) for v in enriched.values())
    print(f"Python SDK: Extracted {pkg_count} packages · {name_count} total exports")


if __name__ == "__main__":
    main()
