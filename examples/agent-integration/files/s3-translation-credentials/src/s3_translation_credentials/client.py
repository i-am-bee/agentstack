# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

"""
Demo client for the S3 credentials translation agent.

The client injects short-lived STS-style S3 credentials into the message
metadata. The agent uses those credentials to upload the translated file
and returns a presigned GET URL — no S3 SDK is needed to download the result.

Usage:
    uv run client input.txt
    uv run client input.txt --user-id bob
    uv run client input.txt --agent-url http://localhost:8001

Prerequisites:
    Copy .env.example to .env and set the S3 connection variables, or export them directly.
    Start the agent first: uv run server
"""

from __future__ import annotations

import base64
import os
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv

load_dotenv()

import asyncclick as click
import httpx
from a2a.client import A2AClient
from a2a.types import (
    FilePart,
    FileWithBytes,
    FileWithUri,
    Message,
    MessageSendParams,
    Part,
    Role,
    SendMessageRequest,
    TextPart,
)
from agentstack_sdk.a2a.extensions.storage.s3 import S3Config
from agentstack_sdk.a2a.extensions.storage.s3_credentials import S3CredentialsExtensionClient


@click.command()
@click.argument("input_file")
@click.option("--user-id", default="alice", show_default=True, help="User ID embedded in the context label.")
@click.option(
    "--agent-url",
    default="http://127.0.0.1:8000/jsonrpc/",
    show_default=True,
    help="Base URL of the running translation agent.",
)
async def run(input_file: str, user_id: str, agent_url: str) -> None:
    config = S3Config(
        endpoint_url=os.environ["S3_ENDPOINT"],
        bucket=os.environ["S3_BUCKET"],
        access_key=os.environ["S3_ACCESS_KEY"],
        secret_key=os.environ["S3_SECRET_KEY"],
    )

    # Each run uses a fresh context_id; the agent will upload to
    # contexts/{context_id}/translated.txt
    context_id = str(uuid4())
    s3_client = S3CredentialsExtensionClient(config=config, context_id=context_id)

    print(f"[{user_id}] Using context_id={context_id}")
    print(f"[{user_id}] Agent will upload to: contexts/{context_id}/translated.txt")

    content = Path(input_file).read_bytes()
    message = Message(
        message_id=str(uuid4()),
        role=Role.user,
        parts=[
            Part(
                root=FilePart(
                    file=FileWithBytes(
                        name=Path(input_file).name,
                        bytes=base64.b64encode(content).decode(),
                        mime_type="text/plain",
                    )
                )
            )
        ],
        metadata={
            "user-id": user_id,
            **s3_client.metadata(),
        },
    )

    async with httpx.AsyncClient() as http:
        client = A2AClient(httpx_client=http, url=agent_url)
        await client.get_card()

        print(f"[{user_id}] Sending file to agent...")
        response = await client.send_message(
            request=SendMessageRequest(id=str(uuid4()), params=MessageSendParams(message=message))
        )

        for event in response.root.result.history or []:
            for part in event.parts or []:
                part_root = part.root
                if isinstance(part_root, FilePart) and isinstance(part_root.file, FileWithUri):
                    download_url = str(part_root.file.uri)
                    print(f"[{user_id}] Downloading result from: {download_url}")
                    result_resp = httpx.get(download_url)
                    result_resp.raise_for_status()
                    print(f"[{user_id}] Translated content:\n{result_resp.text}")
                elif isinstance(part_root, TextPart):
                    print(f"[{user_id}] Agent message: {part_root.text}")


if __name__ == "__main__":
    run()
