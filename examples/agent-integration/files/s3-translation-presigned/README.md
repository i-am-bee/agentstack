# S3 Translation — Pre-signed URL example

Demonstrates the **S3 extension** (`S3ExtensionSpec`) where the client pre-generates presigned PUT/GET URL pairs and injects them into the message metadata as named **slots**. The agent holds no S3 credentials — it receives ready-to-use URLs and writes to them over plain HTTPS.

This example produces **two output files** per request: the translated text and a plain-text stats summary.

## How it works

```
Client                                  S3 / MinIO
  │
  │  1. create_upload_slot("translated", ...)
  │     create_upload_slot("summary", ...)   ──> generates presigned
  │ <─────────────────────────────────────── PUT + GET URL pair × 2
  │
  │  2. SendMessage(FileWithBytes + metadata{
  │       "translated": { upload_url, download_url },
  │       "summary":    { upload_url, download_url }
  │     })
  │ ──────────────────────> Agent
  │                           │
  │                     3. PUT upload_url["translated"] ──> S3
  │                     4. PUT upload_url["summary"]    ──> S3
  │                           │
  │                     5. yield FilePart(translated_download_url)
  │                            FilePart(summary_download_url)
  │ <──────────────────────────
  │
  │  6. GET each download_url ─────────────────────────> S3
  │ <──────────────────────────────────────────────────  content
```

## Slots

A **slot** is a named reservation for one output file, declared by the client before the message is sent. Each slot bundles a presigned PUT URL (for the agent to write) and a presigned GET URL (for anyone to read afterwards).

```python
# Client: declare every file the agent is expected to produce
translated_slot, summary_slot = await asyncio.gather(
    s3_client.create_upload_slot(slot="translated", ...),
    s3_client.create_upload_slot(slot="summary", ...),
)
message.metadata = s3_client.metadata({
    "translated": translated_slot,
    "summary":    summary_slot,
})

# Agent: write to each slot by name
translated_url = await s3.upload(slot="translated", content=..., content_type="text/plain")
summary_url    = await s3.upload(slot="summary",    content=..., content_type="text/plain")
```

The S3 key for each slot is scoped to `{context_id}/{user_id}/{filename}`, ensuring users cannot overwrite each other's files.

## On-demand uploads

This model requires the client to **declare all output files upfront**. If the number of outputs is not known ahead of time — for example, an agent that splits a document into an arbitrary number of chunks — this is a limitation: the agent cannot request new upload URLs mid-stream.

Two approaches for on-demand uploads:

1. **Pre-allocate generously.** If the upper bound is known (e.g. at most 10 chunks), the client creates 10 slots and the agent uses only what it needs. Unused slots simply go unused.

2. **Use the credentials extension.** Inject short-lived IAM-scoped credentials instead of URL pairs. The agent can then create as many objects as it needs within its assigned prefix with no prior negotiation. See [`s3-translation-credentials/`](../s3-translation-credentials/).

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- A running S3-compatible storage backend

Start MinIO locally:

```bash
docker run -p 9000:9000 \
  -e MINIO_ROOT_USER=admin \
  -e MINIO_ROOT_PASSWORD=password \
  minio/minio server /data
```

## Setup

```bash
cp .env.example .env   # adjust values if needed
uv sync
```

## Run

In one terminal, start the agent:

```bash
uv run server
```

In another terminal, send a file:

```bash
uv run client input.txt
uv run client input.txt --user-id bob
uv run client input.txt --agent-url http://localhost:8001
```

The agent produces two files: `translated_<name>.txt` (each line reversed) and `summary.txt` (line / word / char counts). The client downloads and prints both.

## Extension classes

| Class | Role |
|---|---|
| `S3ExtensionClient` | Client-side — calls `create_upload_slot()` per file, builds message metadata |
| `S3ExtensionServer` | Agent-side — calls `upload(slot, content)` per file, returns download URL |
| `S3ExtensionMetadata` | Metadata schema carried in `message.metadata` |
| `S3UploadSlot` | A presigned PUT + GET URL pair for one file |
