# Step 6b – Adapt File Inputs

If the original agent reads files from the local filesystem or accepts file paths as CLI/function arguments, those inputs must be replaced with platform file uploads. Local filesystem access is not available at runtime. If none of the indicators below are found, skip this step.

**Important:** Even if the file contains plain text that _could_ be pasted into the message, still convert the input to a `FileField` upload. The user expects to upload files the same way the original agent consumed them. Do not silently flatten file inputs into message text.

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

If the agent needs **text** from non-plaintext files (PDFs, DOCX, XLSX, PPTX, images, HTML), the platform provides server-side extraction (Docling-backed, including OCR for images).

**Decision gate:** If the original agent already uses a text extraction library (e.g., `PyMuPDF`/`fitz`, `pytesseract`, `pdfplumber`, `python-docx`, `unstructured`), **ask the user** whether to:

1. **Keep the existing library** — load raw bytes via `file.load_content()` and pass them to the agent's existing extraction code.
2. **Switch to platform extraction** — remove the client-side library and use `file.create_extraction()` → poll `file.get_extraction()` until `status == "completed"` → read text via `file.load_text_content()`.

If the agent has no existing extraction, default to platform extraction. For plain text and CSV files, no extraction is needed — use `file.load_content()` directly.

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
