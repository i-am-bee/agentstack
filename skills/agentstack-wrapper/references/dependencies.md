# Dependency Setup Reference

Use this reference for Step 3 dependency decisions, installation flow, version pinning, and import recovery.

## Dependency Workflow

1. Find the existing dependency file:
   - `requirements.txt` → append `agentstack-sdk~=<VERSION>`
   - `pyproject.toml` → add to `[project.dependencies]` or `[tool.poetry.dependencies]`
   - add `a2a-sdk` only when direct pinning is required by the project dependency policy
2. **Select and pin a trusted version (required).** If the current interpreter is unsupported, select a local interpreter that can install `agentstack-sdk` and use that same interpreter for all dependency commands via `python -m pip`. If the project already pins `agentstack-sdk` in its lockfile/constraints or active environment, use that compatible version and keep consistency with the project. If no version is present, use the latest compatible stable released `agentstack-sdk` version from trusted PyPI metadata, then pin with `~=`.
   If the project requires direct `a2a-sdk` pinning, use a version compatible with the selected `agentstack-sdk` dependency constraints.
3. **Install the dependencies.** Once added to the manifest, install them in your virtual environment (e.g., `pip install -qq -r requirements.txt`).
4. **Do not** create a new manifest type the project doesn't already use.
5. **Do not** force `uv` if the project uses `pip`.

## Version Pins

- `agentstack-sdk`
  - If already pinned compatibly: keep it.
  - Otherwise: pin a trusted stable release with `~=`.
  - To resolve latest stable reliably, run `python -m pip install -qq --upgrade agentstack-sdk`, read the installed version with `python -m pip show agentstack-sdk`, then write `agentstack-sdk~=<resolved_version>` to the existing manifest.
- `a2a-sdk`
  - If the project directly manages it: keep/add a version compatible with the selected `agentstack-sdk`.
  - If not: do not add a direct pin.
- Never bump `a2a-sdk` just to follow "latest" when constraints disagree.

**Source-of-truth rule:** The installed package inspection (**Inline Package Search**) is the absolute authority for imports, class names, and types. Use official documentation only for architectural patterns and general logic. If they conflict, follow the introspection result without exception.

**Security rule:** Do not execute remote installation scripts. Use only the repository's existing dependency workflow and trusted package sources.

## Discovering Exact Import Paths (Required)

**Primary Method (Inline Package Search):**
To figure out exact imports from installed libraries (`agentstack_sdk`, `a2a`), you **must** use inline Python execution (`python -c`) to map imports without polluting the project repository. Do not guess import paths or rely solely on documentation if the package is installed.

Run this snippet **once** to crawl the installed package for `agentstack_sdk` and print out all available classes and their exact import paths. Let the full output load into your context so you can resolve all multiple imports instantly without running the script again:

```bash
.venv/bin/python -c "import pkgutil, inspect, agentstack_sdk as sdk; classes = {}; [classes.update({n: f'{m.name}.{n}' for n, o in inspect.getmembers(__import__(m.name, fromlist=['*']), inspect.isclass)}) for m in pkgutil.walk_packages(sdk.__path__, sdk.__name__ + '.')]; [print(path) for path in sorted(classes.values())]"
```

**Fallback Method (Documentation Search):**
If the packages are not installed and cannot be inspected at runtime, attempt to find the exact import path, class names, method names, and properties in the official Agent Stack documentation. Use your web search or documentation reading tools to locate the correct information.

## Import Recovery Sequence (required)

If import validation fails (e.g., `ModuleNotFoundError` or `ImportError`), follow this exact workflow:

1. **Verify Installation:** Ensure `agentstack-sdk` and `a2a` actually exist in the active virtual environment manifest and are installed.
2. **Scan Package Content (Primary Recovery Step):** Immediately use the **Inline Package Search** scripts (shown above) to crawl the installed `.venv`. This will give you the exact, currently installed path for the class that failed to import. Do not guess or hallucinate secondary paths.
3. **Update Code:** Replace the failed import in your code with the exact path returned by the scan.
4. **Fallback:** If the class doesn't exist in the scan results at all, check the official Agent Stack documentation to see if the class name or extension design has fundamentally changed.
5. If imports still fail after taking these steps, stop and report unresolved imports with module names and file paths to the user.
