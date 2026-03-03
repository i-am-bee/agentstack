# Step 6b – Adapt File Inputs

If the original agent reads files from the local filesystem or accepts file paths as CLI/function arguments, those inputs must be replaced with platform file uploads. Local filesystem access is not available at runtime. If none of the indicators below are found, skip this step.

**Important:** Even if the file contains plain text that _could_ be pasted into the message, still convert the input to a `FileField` upload. The user expects to upload files the same way the original agent consumed them. Do not silently flatten file inputs into message text.

## Table of Contents

- [Step 6b – Adapt File Inputs](#step-6b--adapt-file-inputs)
  - [Table of Contents](#table-of-contents)
  - [Detection](#detection)
  - [Replacing File Inputs](#replacing-file-inputs)
  - [Default MIME Type Strategy](#default-mime-type-strategy)
  - [Text Extraction for Documents and Images](#text-extraction-for-documents-and-images)
  - [Minimal Robust Example (Form Upload + Extraction)](#minimal-robust-example-form-upload--extraction)
    - [Example Notes](#example-notes)
    - [Content-Type Branching (Required When Using Broad MIME List)](#content-type-branching-required-when-using-broad-mime-list)
  - [Mid-Conversation File Uploads (Multi-Turn)](#mid-conversation-file-uploads-multi-turn)
  - [Final Validation Checks](#final-validation-checks)
    - [File Upload Surface Rule](#file-upload-surface-rule)
  - [Anti-patterns](#anti-patterns)

## Detection

Scan the original code for: `open()`, `pathlib.Path.read_*()`, `with open(...)`, `argparse` with `type=argparse.FileType`, CLI arguments that accept file paths, or library calls reading from disk (`PIL.Image.open()`, `fitz.open()`, `pandas.read_csv()`, `docx.Document()`, etc.).

## Replacing File Inputs

1. Add a `FileField` (from `agentstack_sdk.a2a.extensions.common.form`) to the form with appropriate `accept` MIME types matching the original agent's supported file types. Use `FileInfo` in the Pydantic model (`list[FileInfo] | None`).
2. Parse the form via `form.parse_initial_form(model=...)` (same as Step 6).
3. Resolve `FileInfo.uri` (an `agentstack://` URI) to a `File` object: extract the file ID using `PlatformFileUrl(file.uri)`, then call `File.get(file_id)`.
4. Load file content via `file.load_content()` (raw bytes) or `file.load_text_content()` (extracted text).
5. The platform `File` API requires `PlatformApiExtensionSpec` declared as an agent parameter (see Step 7 extensions table).

**Important:** The exact calling conventions for `load_content()`, `load_text_content()`, `create_extraction()`, and `get_extraction()` **MUST** be verified by reading the [Working with Files](https://agentstack.beeai.dev/stable/agent-integration/files.md) documentation before implementation. Do not guess return types, async patterns, or attribute names.

See the [form agent](https://github.com/i-am-bee/agentstack/blob/main/agents/form/src/form/agent.py) for `FileField` usage and the [Working with Files](https://agentstack.beeai.dev/stable/agent-integration/files.md) guide for the full File API.

## Default MIME Type Strategy

Do **not** restrict `accept` MIME types to only the format the source agent happened to use, unless the agent explicitly requires that specific format (e.g., it processes raw image pixels via PIL, parses binary structures, or the user has stated a specific format requirement).

**Decision rule:**

- If the source agent is a **text-processing agent** (its core logic operates on text content regardless of source format) → use the **broad MIME list** below.
- If the source agent **explicitly requires a specific file format** for its processing (e.g., it uses `PIL` to manipulate image pixels, or `pandas` to parse CSV structure) → restrict `accept` to that format's MIME type(s).

**Broad MIME list** (default for text-processing agents):

```python
accept=[
    "text/*",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/msword",
    "application/vnd.ms-excel",
    "application/vnd.ms-powerpoint",
    "image/*",
]
```

When using the broad MIME list, the agent handler **must** implement the text extraction pipeline (see below) for non-plaintext uploads. Update form labels and agent descriptions to reflect the broader file acceptance (e.g., "Upload a file" instead of "Upload a text file").

## Text Extraction for Documents and Images

If the agent needs **text** from non-plaintext files (PDFs, DOCX, XLSX, PPTX, images, HTML), platform extraction is available (Docling-backed, including OCR for images).

**Decision gate:** If the original agent already uses a text extraction library (for example `PyMuPDF`/`fitz`, `pytesseract`, `pdfplumber`, `python-docx`, `unstructured`), **ask the user** whether to keep the existing extraction path or switch to platform extraction.

When uploaded files are provided via `FileField`, use this required strategy:

1. Determine the file `content_type`.
2. For plain-text-like types (`text/*`, `text/csv`), attempt direct read first.
3. For document/image types, run extraction: call `create_extraction()` and poll `get_extraction()` until `status == "completed"`.
4. Handle extraction `failed` status explicitly with a clear error.
5. If extracted output is unavailable or unreadable, fallback to `file.load_text_content()` on the original uploaded file.
6. If text still cannot be read, raise an explicit error; do not silently decode arbitrary binary content.

If there is no existing extraction library in the agent, default to platform extraction.

## Minimal Robust Example (Form Upload + Extraction)

Use this as a minimal reference implementation for `FileField` handling:

```python
from pydantic import BaseModel
from typing import Annotated

from a2a.types import Message
from agentstack_sdk.a2a.extensions.common.form import FileField, FileInfo, FormRender
from agentstack_sdk.a2a.extensions.services.form import FormServiceExtensionServer, FormServiceExtensionSpec
from agentstack_sdk.a2a.extensions.services.platform import PlatformApiExtensionServer, PlatformApiExtensionSpec
from agentstack_sdk.platform import File
from agentstack_sdk.platform.file import PlatformFileUrl


class UploadForm(BaseModel):
    input_file: list[FileInfo] | None = None


async def load_uploaded_text(
    form: FormServiceExtensionServer,
    _platform: Annotated[PlatformApiExtensionServer, PlatformApiExtensionSpec()],
) -> str:
    form_data = form.parse_initial_form(model=UploadForm)
    if form_data is None or not form_data.input_file:
        raise ValueError("No file uploaded.")

    first = form_data.input_file[0]

    # Robust shape handling: some paths may return dict-like values
    if isinstance(first, dict):
        file_uri = first.get("uri")
    else:
        file_uri = getattr(first, "uri", None)

    if not file_uri:
        raise ValueError("Uploaded file is missing URI.")

    file_id = PlatformFileUrl(file_uri).file_id
    uploaded_file = await File.get(file_id)
    content_type = (uploaded_file.content_type or "").lower()

    is_plain_text_like = content_type.startswith("text/") or content_type in {"text/csv"}

    if is_plain_text_like:
        async with uploaded_file.load_content() as content:
            if content.text:
                return content.text

    # Extraction path for docs/images and fallback for unreadable plain text
    extraction = await uploaded_file.create_extraction()

    while True:
        extraction = await uploaded_file.get_extraction()
        if extraction.status == "completed":
            break
        if extraction.status == "failed":
            raise RuntimeError("File extraction failed.")

    # Preferred: read extracted text output first
    try:
        if extraction.extracted_files:
            for extracted_file_info in extraction.extracted_files:
                extracted_file = await File.get(extracted_file_info.file_id)
                async with extracted_file.load_content() as extracted_content:
                    if extracted_content.text:
                        return extracted_content.text
    except Exception:
        pass

    # Fallback: platform text loader on original file
    text = await uploaded_file.load_text_content()
    if text:
        return text

    raise RuntimeError("Could not read text from uploaded file.")


# Example FileField (text-processing agent):
initial_form = FormRender(
    title="Upload a file",
    fields=[
        FileField(
            id="input_file",
            label="Upload a file",
            required=True,
            accept=[
                "text/*",
                "application/pdf",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/msword",
                "image/*",
            ],
        )
    ],
)
```

### Example Notes

- Keep this example minimal; adapt only the `accept` list when the original agent is truly format-specific.
- Always keep the dict-or-object URI access guard to avoid `"dict" object has no attribute "uri"` failures.
- Prefer explicit errors over silent fallbacks that hide extraction failures.

### Content-Type Branching (Required When Using Broad MIME List)

When the `FileField` accepts multiple MIME types, the agent handler must branch on the resolved `File` object's `content_type` field to decide how to load content:

1. **Plain text / CSV** (`text/*`, `text/csv`) → load directly via `file.load_content()`, read `.text`.
2. **Documents and images** (`application/pdf`, `application/vnd.openxmlformats-*`, `image/*`, etc.) → trigger platform extraction:
   - Call `file.create_extraction()` to start server-side text extraction.
   - Poll `file.get_extraction()` until `status == "completed"` (handle `"failed"` with a clear error).
   - Read extracted text via `file.load_text_content()`.

Do not assume all uploaded files are plain text. Always check `content_type` before choosing the loading strategy.

See the [Text extraction](https://agentstack.beeai.dev/stable/agent-integration/rag.md#text-extraction) section of the RAG guide for the full extraction pipeline and API details.

## Mid-Conversation File Uploads (Multi-Turn)

For multi-turn agents receiving files during conversation (not via initial form), files arrive as `FilePart` entries in A2A message history. Extract them by filtering `FilePart` with `FileWithUri`, parsing the `agentstack://` URI via `PlatformFileUrl`, and resolving with `File.get()`.

See the [Working with Files](https://agentstack.beeai.dev/stable/agent-integration/files.md) guide for the full API and examples.

## Final Validation Checks

Before marking Step 6b complete, verify all checks below:

- [ ] Content-type branching exists (`text/*`/`text/csv` direct read, docs/images extraction path).
- [ ] `create_extraction()` + polling `get_extraction()` handles both `completed` and `failed`.
- [ ] Extraction-read fallback exists (`file.load_text_content()` on original file).
- [ ] Explicit error is raised if text cannot be obtained.
- [ ] No `default_input_modes`/`default_output_modes` unless direct chat file I/O is intentionally required.

### File Upload Surface Rule

If files are intended to be submitted only through an initial form (`FileField`), do **not** add broad `default_input_modes` just to satisfy file adaptation. `default_input_modes` should be added only when the agent is intentionally designed to accept `FilePart` uploads directly in chat messages.

Similarly, do not add `default_output_modes` unless the agent actually yields file outputs/artifacts.

## Anti-patterns

- **Never assume extracted file IDs are always readable.** If reading extracted text output fails, attempt `file.load_text_content()` on the original file before failing.
- **Never force extraction-first for plain text files.** Read direct text first for plain-text-like content types.
- **Never enable `default_output_modes` unless the agent emits file outputs.** Keep output modes minimal and behavior-driven.
- **Never add `default_input_modes` for form-only file uploads unless direct chat file upload is an explicit requirement.**
