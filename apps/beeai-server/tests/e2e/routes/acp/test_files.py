# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import pytest
from acp_sdk import MessagePart, Message
from acp_sdk.client import Client
from acp_sdk.server import Server
from pydantic import AnyUrl

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
async def test_file_reader_public_url(server: Server, acp_client: Client) -> None:
    # Try downloading public url
    url = "https://raw.githubusercontent.com/i-am-bee/beeai-platform/refs/heads/main/README.md"
    response = await acp_client.run_sync(
        agent="file_reader",
        input=[Message(parts=[MessagePart(content_url=AnyUrl(url))])],
    )
    assert "beeai" in response.output[0].parts[0].content.lower()


@pytest.mark.asyncio
async def test_file_reader_platform_file(server: Server, api_client, acp_client: Client) -> None:
    # Try downloading public url
    response = await api_client.post("files", files={"file": ("test.txt", "Hello world", "custom/type")})
    response.raise_for_status()
    file_id = response.json()["id"]
    content_url = f"http://{{platform_url}}/api/v1/files/{file_id}/content"

    response = await acp_client.run_sync(
        agent="file_reader",
        input=[Message(parts=[MessagePart(content_url=AnyUrl(content_url))])],
    )
    assert response.output[0].parts[0].content == "Hello world"
    assert response.output[0].parts[0].content_type == "custom/type"
