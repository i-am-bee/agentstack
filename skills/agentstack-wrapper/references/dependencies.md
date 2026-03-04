# Dependency Setup Reference

Use this reference for Step 3 dependency decisions, installation flow, version pinning, and import recovery.

## Dependency Workflow

1. Find the existing dependency file:
   - `requirements.txt` → append `agentstack-sdk~=<VERSION>`
   - `pyproject.toml` → add to `[project.dependencies]` or `[tool.poetry.dependencies]`
   - add `a2a-sdk` only when direct pinning is required by the project dependency policy
2. **Select and pin a trusted version (required).** If the current interpreter is unsupported, select a local interpreter that can install `agentstack-sdk` and use that same interpreter for all dependency commands via `python -m pip`. If the project already pins `agentstack-sdk` in its lockfile/constraints or active environment, use that compatible version and keep consistency with the project. If no version is present, use the latest compatible stable released `agentstack-sdk` version from trusted PyPI metadata, then pin with `~=`.
   If the project requires direct `a2a-sdk` pinning, use a version compatible with the selected `agentstack-sdk` dependency constraints.
3. **Install the dependencies.** Once added to the manifest, install them in your virtual environment (e.g., `pip install -r requirements.txt`).
4. **Do not** create a new manifest type the project doesn't already use.
5. **Do not** force `uv` if the project uses `pip`.

## Version Pins

- `agentstack-sdk`
  - If already pinned compatibly: keep it.
  - Otherwise: pin a trusted stable release with `~=`.
  - To resolve latest stable reliably, run `python -m pip install --upgrade agentstack-sdk`, read the installed version with `python -m pip show agentstack-sdk`, then write `agentstack-sdk~=<resolved_version>` to the existing manifest.
- `a2a-sdk`
  - If the project directly manages it: keep/add a version compatible with the selected `agentstack-sdk`.
  - If not: do not add a direct pin.
- Never bump `a2a-sdk` just to follow "latest" when constraints disagree.

**Source-of-truth rule:** Use current official docs and installed package inspection as the authority. If they conflict, follow installed package behavior and report the mismatch.

**Security rule:** Do not execute remote installation scripts. Use only the repository's existing dependency workflow and trusted package sources.

## Import Recovery Sequence (required)

If import validation fails, follow this exact order:

1. Run import validation to identify missing modules.
2. If a missing import is caused by absent dependencies, install or repair dependencies in the existing manifest workflow.
3. Re-run import validation after dependency repair.
4. If imports still fail, stop and report unresolved imports with module names and file paths.

## Exploring Unknown Packages Without Test Files (Zero-File Discovery)

**Primary Method (Documentation Search):**
First, you MUST attempt to find the exact import path, class names, method names, and properties in the official Agent Stack documentation. Use your web search or documentation reading tools to locate the correct information.

**Fallback Method (Inline Package Search):**
If you need to figure out exact imports from installed libraries (`agentstack_sdk`, `a2a`) but docs are unavailable, **do not create temporary test scripts**. Instead, use inline Python execution (`python -c`) or your native search tools to map imports without polluting the project repository.

Use this approach **only** if you ran the code and it failed due to a missing or incorrect import. You have several options for inline exploration depending on what you need:

**1. Quick Overview with `dir()`:**
The simplest way to see what's available in a module is the built-in `dir()` function, which returns a list of all names (variables, functions, classes, modules) in the given object's namespace.

```bash
python -c 'import agentstack_sdk; print(dir(agentstack_sdk))'
```

_Note: This will also show internal attributes (starting with an underscore), which you generally should avoid using._

**2. Official Exports with `__all__`:**
Many well-written packages define an `__all__` list, specifying strictly what should be exported as the public API.

```bash
python -c 'import agentstack_sdk; print(getattr(agentstack_sdk, "__all__", "Module does not define __all__, use dir()"))'
```

**3. Deep Search (for nested/hidden classes):**
**Last Resort:** If you know the exact name of the target class but cannot find its import path in the documentation, use this snippet to crawl the package:

```bash
python -c '
import pkgutil, importlib
def find_class(pkg_name, target):
    pkg = importlib.import_module(pkg_name)
    for _, modname, _ in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
        try:
            if hasattr(importlib.import_module(modname), target):
                print(f"Found {target} in: {modname}")
        except Exception:
            pass
find_class("agentstack_sdk", "AgentDetail")
'
```

Once the module is located, you can inspect its signature or docstring directly via another short inline command:

```bash
python -c "from agentstack_sdk.server.agent import AgentDetail; help(AgentDetail)"
```
