# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import httpx
import pytest
from asyncpg.pgproto.pgproto import timedelta
from tenacity import AsyncRetrying, stop_after_delay, wait_fixed

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
@pytest.mark.usefixtures("clean_up")
async def test_files(subtests, setup_real_llm, api_client, acp_client):
    with subtests.test("upload file"):
        response = await api_client.post(
            "files", files={"file": ("test.txt", '{"hello": "world"}', "application/json")}
        )
        response.raise_for_status()
        file_id = response.json()["id"]

    with subtests.test("get file metadata"):
        response = await api_client.get(f"files/{file_id}")
        response.raise_for_status()
        assert response.json()["id"] == file_id

    with subtests.test("get file content"):
        response = await api_client.get(f"files/{file_id}/content")
        response.raise_for_status()
        assert response.json() == {"hello": "world"}
        assert response.headers["Content-Type"] == "application/json"

    with subtests.test("delete file"):
        response = await api_client.delete(f"files/{file_id}")
        response.raise_for_status()
        with pytest.raises(httpx.HTTPStatusError, match="404 Not Found"):
            response = await api_client.get(f"files/{file_id}")
            response.raise_for_status()


@pytest.mark.asyncio
@pytest.mark.usefixtures("clean_up")
async def test_text_extraction_pdf_workflow(subtests, api_client, data_dir):
    """Test complete PDF text extraction workflow: upload -> extract -> wait -> verify"""

    # Create a simple PDF-like content for testing
    # In a real scenario, you would use a proper PDF file

    file_id = None

    with subtests.test("upload PDF file"):
        with open(data_dir / "beeai.pdf", "rb") as f:
            response = await api_client.post("files", files={"file": ("test_document.pdf", f, "application/pdf")})
            response.raise_for_status()
            file_data = response.json()
            file_id = file_data["id"]
            assert file_data["filename"] == "test_document.pdf"
            assert file_data["file_type"] == "user_upload"

    with subtests.test("create text extraction"):
        response = await api_client.post(f"files/{file_id}/extraction")
        response.raise_for_status()
        extraction_data = response.json()
        assert extraction_data["file_id"] == file_id
        assert extraction_data["status"] in ["pending", "in_progress", "completed"]

    with subtests.test("check extraction status"):
        response = await api_client.get(f"files/{file_id}/extraction")
        response.raise_for_status()
        extraction_data = response.json()
        assert extraction_data["file_id"] == file_id

    async for attempt in AsyncRetrying(stop=stop_after_delay(timedelta(seconds=40)), wait=wait_fixed(1)):
        with attempt:
            response = await api_client.get(f"files/{file_id}/extraction")
            response.raise_for_status()
            extraction_data = response.json()
            final_status = extraction_data["status"]
            if final_status not in ["completed", "failed"]:
                raise ValueError("not completed")

    assert final_status == "completed", (
        f"Expected completed status, got {final_status}: {extraction_data['error_message']}"
    )
    assert extraction_data["extracted_file_id"] is not None
    assert extraction_data["finished_at"] is not None

    with subtests.test("verify extracted text content"):
        response = await api_client.get(f"files/{file_id}/text_content")
        response.raise_for_status()

        # Check that we get some text content back
        content = response.text
        assert len(content) > 0, "No text content was extracted"
        assert "Deploy BeeAI to Kubernetes using Helm" in content

    with subtests.test("delete extraction"):
        response = await api_client.delete(f"files/{file_id}/extraction")
        response.raise_for_status()

    with subtests.test("verify extraction deleted"):
        with pytest.raises(httpx.HTTPStatusError, match="404 Not Found"):
            response = await api_client.get(f"files/{file_id}/extraction")
            response.raise_for_status()


@pytest.mark.asyncio
@pytest.mark.usefixtures("clean_up")
async def test_text_extraction_plain_text_workflow(subtests, setup_real_llm, api_client, acp_client):
    """Test text extraction for plain text files (should be immediate)"""

    text_content = "This is a sample text document with some content for testing text extraction."
    file_id = None

    with subtests.test("upload text file"):
        response = await api_client.post("files", files={"file": ("test_document.txt", text_content, "text/plain")})
        response.raise_for_status()
        file_data = response.json()
        file_id = file_data["id"]
        assert file_data["filename"] == "test_document.txt"

    with subtests.test("create text extraction for plain text"):
        response = await api_client.post(f"files/{file_id}/extraction")
        response.raise_for_status()
        extraction_data = response.json()
        assert extraction_data["file_id"] == file_id
        # Plain text files should be completed immediately
        assert extraction_data["status"] == "completed"

    with subtests.test("verify immediate text content access"):
        response = await api_client.get(f"files/{file_id}/text_content")
        response.raise_for_status()

        extracted_content = response.text
        assert extracted_content == text_content
