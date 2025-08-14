# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Callable
from datetime import timedelta
from io import BytesIO

import httpx
import pytest
from beeai_sdk.platform import use_platform_client
from beeai_sdk.platform.client import PlatformClient
from beeai_sdk.platform.context import Context, ContextPermissions
from beeai_sdk.platform.file import File
from tenacity import AsyncRetrying, stop_after_delay, wait_fixed

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
@pytest.mark.usefixtures("clean_up", "setup_platform_client", "setup_real_llm")
async def test_files(subtests):
    with subtests.test("upload file"):
        file = await File.create(
            filename="test.txt",
            content=b'{"hello": "world"}',
            content_type="application/json",
        )
        file_id = file.id

    with subtests.test("get file metadata"):
        retrieved_file = await File.get(file_id)
        assert retrieved_file.id == file_id

    with subtests.test("get file content"):
        async with retrieved_file.load_content() as loaded_file:
            assert loaded_file.text == '{"hello": "world"}'

    with subtests.test("delete file"):
        await File.delete(file_id)
        with pytest.raises(httpx.HTTPStatusError, match="404 Not Found"):
            _ = await File.get(self=file_id)


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
@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_text_extraction_pdf_workflow(subtests, test_configuration, test_pdf: Callable[[str], BytesIO]):
    """Test complete PDF text extraction workflow: upload -> extract -> wait -> verify"""

    # Create a simple PDF-like content for testing
    pdf = test_pdf(
        "Test of sirens\n" * 100 + "\nBeeai is the future of AI\n\nThere is no better platform than the beeai platform."
    )

    with subtests.test("upload PDF file"):
        file = await File.create(
            filename="test_document.pdf",
            content=pdf,
            content_type="application/pdf",
        )
        assert file.filename == "test_document.pdf"
        assert file.file_type == "user_upload"

    with subtests.test("create text extraction"):
        extraction = await file.create_extraction()
        assert extraction.file_id == file.id
        assert extraction.status in ["pending", "in_progress", "completed"]

    with subtests.test("check extraction status"):
        extraction = await file.get_extraction()
        assert extraction.file_id == file.id

    async for attempt in AsyncRetrying(stop=stop_after_delay(timedelta(seconds=40)), wait=wait_fixed(1)):
        with attempt:
            extraction = await file.get_extraction()
            final_status = extraction.status
            if final_status not in ["completed", "failed"]:
                raise ValueError("not completed")

    assert final_status == "completed", f"Expected completed status, got {final_status}: {extraction.error_message}"
    assert extraction.extracted_file_id is not None
    assert extraction.finished_at is not None

    with subtests.test("verify extracted text content"):
        async with file.load_text_content() as text_content:
            # Check that we get some text content back
            assert len(text_content.text) > 0, "No text content was extracted"
            assert "Beeai is the future of AI" in text_content.text

    with subtests.test("delete extraction"):
        await file.delete_extraction()

    with (
        subtests.test("verify extraction deleted"),
        pytest.raises(httpx.HTTPStatusError, match="404 Not Found"),
    ):
        _ = await file.get_extraction()


@pytest.mark.asyncio
@pytest.mark.usefixtures("clean_up", "setup_real_llm", "setup_platform_client")
async def test_text_extraction_plain_text_workflow(subtests):
    """Test text extraction for plain text files (should be immediate)"""
    text_content = "This is a sample text document with some content for testing text extraction."

    with subtests.test("upload text file"):
        file = await File.create(
            filename="test_document.txt",
            content=text_content.encode(),
            content_type="text/plain",
        )
        assert file.filename == "test_document.txt"

    with subtests.test("create text extraction for plain text"):
        extraction = await file.create_extraction()
        assert extraction.file_id == file.id
        # Plain text files should be completed immediately
        assert extraction.status == "completed"

    with subtests.test("verify immediate text content access"):
        async with file.load_text_content() as loaded_text_content:
            assert loaded_text_content.text == text_content


@pytest.mark.asyncio
@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_context_scoped_file_access(subtests):
    """Test that files are properly scoped to contexts and users cannot access files from other contexts."""

    with subtests.test("create two different contexts"):
        ctx1 = await Context.create()
        ctx2 = await Context.create()

    with subtests.test("generate context tokens"):
        permissions = ContextPermissions(files={"read", "write", "extract"})
        token_1 = await ctx1.generate_token(grant_context_permissions=permissions)
        token_2 = await ctx2.generate_token(grant_context_permissions=permissions)

    # Create platform clients with context tokens
    async with (
        PlatformClient(context_id=ctx1.id, auth_token=token_1.token.get_secret_value()) as client_1,
        PlatformClient(context_id=ctx2.id, auth_token=token_2.token.get_secret_value()) as client_2,
    ):
        with subtests.test("upload file in context 1"):
            file_1 = await File.create(
                filename="1.txt",
                content=b"1",
                content_type="text/plain",
                client=client_1,
            )
            assert file_1.filename == "1.txt"
            file_id_1 = file_1.id

        with subtests.test("upload file in context 2"):
            file_2 = await File.create(
                filename="2.txt",
                content=b"2",
                content_type="text/plain",
                client=client_2,
            )
            assert file_2.filename == "2.txt"
            file_id_2 = file_2.id

        # Verify file can be accessed within its own context
        with subtests.test("access file within own context 1"):
            retrieved_file = await File.get(file_id_1, client=client_1)
            assert retrieved_file.id == file_id_1

            async with File.load_content(file_id_1, client=client_1) as loaded_file:
                assert loaded_file.text == "1"

        # Verify file cannot be accessed from different context using wrong client
        with (
            subtests.test("cannot access context 1 file using context 2 client"),
            pytest.raises(httpx.HTTPStatusError, match="404 Not Found|403 Forbidden"),
        ):
            await File.get(file_id_1, client=client_2)

        with (
            subtests.test("cannot access context 1 file content using context 2 client"),
            pytest.raises(httpx.HTTPStatusError, match="404 Not Found|403 Forbidden"),
        ):
            async with File.load_content(file_id_1, client=client_2):
                ...

        # Verify file cannot be deleted from different context using wrong client
        with (
            subtests.test("cannot delete context 1 file using context 2 client"),
            pytest.raises(httpx.HTTPStatusError, match="404 Not Found|403 Forbidden"),
        ):
            await File.delete(file_id_1, client=client_2)

        # Verify cross-context isolation works both ways
        with (
            subtests.test("cannot access context 2 file using context 1 client"),
            pytest.raises(httpx.HTTPStatusError, match="404 Not Found|403 Forbidden"),
        ):
            await File.get(file_id_2, client=client_1)

        # Verify context_id parameter validation - cannot use wrong context_id
        with (
            subtests.test("cannot use wrong context_id with context 1 client"),
            pytest.raises(httpx.HTTPStatusError, match="403 Forbidden"),
        ):
            await File.get(file_id_1, client=client_1, context_id=ctx2.id)

        with (
            subtests.test("cannot use wrong context_id with context 2 client"),
            pytest.raises(httpx.HTTPStatusError, match="403 Forbidden"),
        ):
            await File.get(file_id_2, client=client_2, context_id=ctx1.id)

        # Clean up - delete files in their proper contexts
        with subtests.test("clean up - delete context 1 file"):
            await File.delete(file_id_1, client=client_1)

        with subtests.test("clean up - delete context 2 file"):
            await File.delete(file_id_2, client=client_2)


@pytest.mark.asyncio
@pytest.mark.usefixtures("clean_up")
async def test_file_extraction_context_isolation(subtests, test_configuration):
    """Test that file text extraction is also properly scoped to contexts."""
    base_url = test_configuration.server_url

    with subtests.test("create contexts and tokens"):
        async with use_platform_client(base_url=base_url, auth=("admin", "test-password")):
            ctx1 = await Context.create()
            ctx2 = await Context.create()

            permissions = ContextPermissions(files={"read", "write", "extract"})
            token_1 = await ctx1.generate_token(grant_context_permissions=permissions)
            token_2 = await ctx2.generate_token(grant_context_permissions=permissions)

    # Create platform clients with context tokens
    async with (
        PlatformClient(base_url=base_url, context_id=ctx1.id, auth_token=token_1.token.get_secret_value()) as client_1,
        PlatformClient(base_url=base_url, context_id=ctx2.id, auth_token=token_2.token.get_secret_value()) as client_2,
    ):
        # Upload text file in context 1
        file_id = None
        with subtests.test("upload text file in context 1"):
            file = await File.create(
                filename="test_extraction.txt",
                content=b"Test content for extraction",
                content_type="text/plain",
                client=client_1,
            )
            file_id = file.id

        # Create extraction in context 1
        with subtests.test("create extraction in context 1"):
            extraction = await File.create_extraction(file_id, client=client_1)
            assert extraction.status == "completed"

        # Verify extraction can be accessed in context 1
        with subtests.test("access extraction in context 1"):
            extraction = await File.get_extraction(file_id, client=client_1)
            assert extraction.file_id == file_id

        with subtests.test("access text content in context 1"):
            async with File.load_text_content(file_id, client=client_1) as loaded_content:
                assert loaded_content.text == "Test content for extraction"

        # Verify extraction cannot be accessed from context 2
        with (
            subtests.test("cannot access extraction from context 2"),
            pytest.raises(httpx.HTTPStatusError, match="404 Not Found|403 Forbidden"),
        ):
            await File.get_extraction(file_id, client=client_2)

        with (
            subtests.test("cannot access text content from context 2"),
            pytest.raises(httpx.HTTPStatusError, match="404 Not Found|403 Forbidden"),
        ):
            async with File.load_text_content(file_id, client=client_2):
                ...

        # Verify extraction cannot be created from wrong context
        with (
            subtests.test("cannot create extraction from context 2"),
            pytest.raises(httpx.HTTPStatusError, match="404 Not Found|403 Forbidden"),
        ):
            await File.create_extraction(file_id, client=client_2)

        # Verify extraction cannot be deleted from wrong context
        with (
            subtests.test("cannot delete extraction from context 2"),
            pytest.raises(httpx.HTTPStatusError, match="404 Not Found|403 Forbidden"),
        ):
            await File.delete_extraction(file_id, client=client_2)

        # Clean up
        with subtests.test("clean up - delete extraction"):
            await File.delete_extraction(file_id, client=client_1)

        with subtests.test("clean up - delete file"):
            await File.delete(file_id, client=client_1)
