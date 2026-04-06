# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

"""
Demo client for the S3 translation agent.

Usage:
    uv run client input.txt
    uv run client input.txt --user-id bob
    uv run client input.txt --agent-url http://localhost:8001

Prerequisites:
    Copy .env.example to .env and set the S3 connection variables, or export them directly.
    Start the agent first: uv run server
"""

from __future__ import annotations

import asyncio
import base64
import os
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv

load_dotenv()

import asyncclick as click
import httpx
from a2a.client import A2AClient
from a2a.types import FilePart, FileWithBytes, FileWithUri, Message, Part, Role, TextPart, SendMessageRequest, \
    MessageSendParams
from agentstack_sdk.a2a.extensions.storage.s3 import S3Config, S3ExtensionClient


@click.command()
@click.argument("input_file")
@click.option("--user-id", default="alice", show_default=True, help="User ID to scope the S3 key prefix.")
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
    s3_client = S3ExtensionClient(config=config)

    # Each demo run uses a fresh context_id to scope the S3 keys.
    context_id = str(uuid4())

    # Pre-generate one upload slot per expected output file.
    # The agent can only write to slots declared here — it receives no S3
    # credentials and cannot request additional slots mid-stream.
    translated_slot, summary_slot = await asyncio.gather(
        s3_client.create_upload_slot(
            slot="translated",
            context_id=context_id,
            user_id=user_id,
            filename="translated.txt",
        ),
        s3_client.create_upload_slot(
            slot="summary",
            context_id=context_id,
            user_id=user_id,
            filename="summary.txt",
        ),
    )
    print(f"[{user_id}] Upload slots created under {context_id}/{user_id}/")

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
            **s3_client.metadata({"translated": translated_slot, "summary": summary_slot}),
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
                    label = part_root.file.name or download_url
                    print(f"[{user_id}] Downloading {label} from: {download_url}")
                    result_resp = httpx.get(download_url)
                    result_resp.raise_for_status()
                    print(f"[{user_id}] {label}:\n{result_resp.text}")
                elif isinstance(part_root, TextPart):
                    print(f"[{user_id}] Agent message: {part_root.text}")


if __name__ == "__main__":
    run()
