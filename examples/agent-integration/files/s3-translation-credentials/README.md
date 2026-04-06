# S3 Translation — Credentials example

Demonstrates the **S3 credentials extension** (`S3CredentialsExtensionSpec`) where the client injects short-lived, IAM-scoped credentials directly into the message metadata. The agent uses those credentials to upload freely within its assigned prefix — no slots, no pre-declared filenames. Receivers never need an S3 SDK; they follow a plain HTTPS presigned GET URL returned by the agent.

## How it works

```
Client                                  AWS STS / MinIO
  │
  │  1. (production) AssumeRole with inline policy
  │     scoped to contexts/{context_id}/*
  │ ─────────────────────────────────────────────> returns AccessKeyId,
  │ <───────────────────────────────────────────── SecretAccessKey, SessionToken
  │
  │  2. SendMessage(FileWithBytes + metadata{
  │       endpoint, bucket, access_key_id,
  │       secret_access_key, session_token,
  │       prefix="contexts/{context_id}/"
  │     })
  │ ──────────────────────> Agent
  │                           │
  │                     3. aioboto3.put_object(
  │                           key=prefix+"translated.txt") ──> S3
  │                           │
  │                     4. generate_presigned_url("get_object")
  │                           │
  │                     5. yield FilePart(FileWithUri(presigned_GET_url))
  │ <──────────────────────────
  │
  │  6. GET presigned_GET_url ──────────────────> S3
  │ <─────────────────────────────────────────── file content
```

The client owns the namespace (`contexts/{context_id}/`) and enforces isolation via IAM policy — the agent cannot write outside its assigned prefix. The agent decides the filename at runtime; there is no upfront slot negotiation.

Credential fields (`access_key_id`, `secret_access_key`, `session_token`) are automatically redacted in logs and telemetry.

## Demo vs. production

| | Demo (this example) | Production |
|---|---|---|
| Credentials source | Long-lived keys from `.env` | `S3CredentialsExtensionClient.from_sts(role_arn=...)` |
| Session token | `None` | STS `AssumeRole` response |
| Namespace isolation | Honour system | IAM policy enforced by AWS |

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

The agent reverses each line of the input file (mock translation), uploads the result to `contexts/{context_id}/translated.txt` using the injected credentials, and returns a presigned GET URL. The client downloads and prints the translated content.

## Extension classes

| Class | Role |
|---|---|
| `S3CredentialsExtensionClient` | Client-side — builds metadata with credentials + prefix; `from_sts()` for production |
| `S3CredentialsExtensionServer` | Agent-side — calls `upload(filename, content)`, returns presigned GET URL |
| `S3CredentialsExtensionMetadata` | Metadata schema carried in `message.metadata`; secrets redacted in logs |
