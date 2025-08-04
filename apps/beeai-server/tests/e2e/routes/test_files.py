# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Callable
from datetime import timedelta
from io import BytesIO

import httpx
import pytest
from beeai_sdk.platform.file import File
from tenacity import AsyncRetrying, stop_after_delay, wait_fixed

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
@pytest.mark.usefixtures("clean_up")
async def test_files(subtests, setup_real_llm, api_client):
    with subtests.test("upload file"):
        file = await File.create(
            filename="test.txt", content=b'{"hello": "world"}', content_type="application/json", client=api_client
        )
        file_id = file.id

    with subtests.test("get file metadata"):
        retrieved_file = await File.get(file_id, client=api_client)
        assert retrieved_file.id == file_id

    with subtests.test("get file content"):
        content = await retrieved_file.content(client=api_client)
        assert content == '{"hello": "world"}'

    with subtests.test("delete file"):
        await File.delete(file_id, client=api_client)
        with pytest.raises(httpx.HTTPStatusError, match="404 Not Found"):
            await File.get(file_id, client=api_client)


@pytest.fixture
def test_pdf() -> Callable[[str], BytesIO]:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    def create_fn(text: str) -> BytesIO:
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter, initialFontSize=12)
        x, y, max_y = 100, 750, 50
        for line in text.split("\n"):
            c.drawString(x, y, line)
            y -= 15
            if y < max_y:
                c.showPage()
                y = 750
        c.save()
        buffer.seek(0)
        return buffer

    return create_fn


@pytest.mark.asyncio
@pytest.mark.usefixtures("clean_up")
async def test_text_extraction_pdf_workflow(subtests, api_client, test_pdf: Callable[[str], BytesIO]):
    """Test complete PDF text extraction workflow: upload -> extract -> wait -> verify"""

    # Create a simple PDF-like content for testing
    pdf = test_pdf(
        "Test of sirens\n" * 100 + "\nBeeai is the future of AI\n\nThere is no better platform than the beeai platform."
    )

    with subtests.test("upload PDF file"):
        file = await File.create(
            filename="test_document.pdf", content=pdf, content_type="application/pdf", client=api_client
        )
        assert file.filename == "test_document.pdf"
        assert file.file_type == "user_upload"

    with subtests.test("create text extraction"):
        extraction = await file.create_extraction(client=api_client)
        assert extraction.file_id == file.id
        assert extraction.status in ["pending", "in_progress", "completed"]

    with subtests.test("check extraction status"):
        extraction = await file.get_extraction(client=api_client)
        assert extraction.file_id == file.id

    async for attempt in AsyncRetrying(stop=stop_after_delay(timedelta(seconds=40)), wait=wait_fixed(1)):
        with attempt:
            extraction = await file.get_extraction(client=api_client)
            final_status = extraction.status
            if final_status not in ["completed", "failed"]:
                raise ValueError("not completed")

    assert final_status == "completed", f"Expected completed status, got {final_status}: {extraction.error_message}"
    assert extraction.extracted_file_id is not None
    assert extraction.finished_at is not None

    with subtests.test("verify extracted text content"):
        content = await file.text_content(client=api_client)

        # Check that we get some text content back
        assert len(content) > 0, "No text content was extracted"
        assert "Beeai is the future of AI" in content

    with subtests.test("delete extraction"):
        await file.delete_extraction(client=api_client)

    with (
        subtests.test("verify extraction deleted"),
        pytest.raises(httpx.HTTPStatusError, match="404 Not Found"),
    ):
        await file.get_extraction(client=api_client)


@pytest.mark.asyncio
@pytest.mark.usefixtures("clean_up")
async def test_text_extraction_plain_text_workflow(subtests, setup_real_llm, api_client):
    """Test text extraction for plain text files (should be immediate)"""

    text_content = "This is a sample text document with some content for testing text extraction."

    with subtests.test("upload text file"):
        file = await File.create(
            filename="test_document.txt", content=text_content.encode(), content_type="text/plain", client=api_client
        )
        assert file.filename == "test_document.txt"

    with subtests.test("create text extraction for plain text"):
        extraction = await file.create_extraction(client=api_client)
        assert extraction.file_id == file.id
        # Plain text files should be completed immediately
        assert extraction.status == "completed"

    with subtests.test("verify immediate text content access"):
        extracted_content = await file.text_content(client=api_client)
        assert extracted_content == text_content
