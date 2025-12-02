# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import json
from collections.abc import Callable
from datetime import timedelta
from io import BytesIO

import httpx
import pytest
from agentstack_sdk.platform import use_platform_client
from agentstack_sdk.platform.client import PlatformClient
from agentstack_sdk.platform.context import Context, ContextPermissions
from agentstack_sdk.platform.file import File
from httpx import AsyncClient
from tenacity import AsyncRetrying, stop_after_delay, wait_fixed

from agentstack_server.domain.models.file import ExtractionFormat

pytestmark = pytest.mark.e2e


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


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_text_extraction_pdf_workflow(subtests, test_configuration, test_pdf: Callable[[str], BytesIO]):
    """Test complete PDF text extraction workflow: upload -> extract -> wait -> verify"""

    # Create a simple PDF-like content for testing
    pdf = test_pdf(
        "Test of sirens\n" * 100 + "\nAgent Stack is the future of AI\n\nThere is no better platform than Agent Stack."
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
    assert extraction.finished_at is not None

    extracted_files = {f.format: f for f in extraction.extracted_files}
    assert set(extracted_files.keys()) == {
        ExtractionFormat.MARKDOWN,
        ExtractionFormat.VENDOR_SPECIFIC_JSON,
    }, "Unexpected extracted file formats"

    with subtests.test("verify extracted files"):
        for extracted_file in extracted_files.values():
            if extracted_file.format == ExtractionFormat.MARKDOWN:
                async with File.load_content(extracted_file.file_id) as markdown_file:
                    assert markdown_file.text is not None, "Markdown file has no content"

            elif extracted_file.format == ExtractionFormat.VENDOR_SPECIFIC_JSON:
                async with File.load_content(extracted_file.file_id) as json_file:
                    assert json_file.text is not None, "JSON file has no content"
                    json_value = json.loads(json_file.text)

                    assert "schema_name" in json_value, "Missing 'schema_name' key"
                    assert json_value["schema_name"] == "DoclingDocument", (
                        f"Expected 'DoclingDocument', got '{json_value['schema_name']}'"
                    )

    with subtests.test("verify extracted text content"):
        async with file.load_text_content() as text_content:
            # Check that we get some text content back
            assert len(text_content.text) > 0, "No text content was extracted"
            assert "Agent Stack is the future of AI" in text_content.text

    with subtests.test("delete extraction"):
        await file.delete_extraction()

    with (
        subtests.test("verify extraction deleted"),
        pytest.raises(httpx.HTTPStatusError, match="404 Not Found"),
    ):
        _ = await file.get_extraction()

    with (
        subtests.test("verify markdown file deleted"),
        pytest.raises(httpx.HTTPStatusError, match="404 Not Found"),
    ):
        async with File.load_content(extracted_files[ExtractionFormat.MARKDOWN].file_id):
            ...

    with (
        subtests.test("verify vendor specific json file deleted"),
        pytest.raises(httpx.HTTPStatusError, match="404 Not Found"),
    ):
        async with File.load_content(extracted_files[ExtractionFormat.VENDOR_SPECIFIC_JSON].file_id):
            ...


@pytest.mark.usefixtures("clean_up", "setup_real_llm", "setup_platform_client")
async def test_text_extraction_plain_text_workflow(subtests):
    """Test text extraction for plain text files also generate json and markdown outputs."""
    text_content = "This is a sample text document with some content for testing text extraction."

    with subtests.test("upload text file"):
        file = await File.create(
            filename="test_document.txt",
            content=text_content.encode(),
            content_type="text/plain",
        )
        assert file.filename == "test_document.txt"
        assert file.file_type == "user_upload"

    with subtests.test("create text extraction for plain text"):
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
    assert extraction.finished_at is not None

    [extracted_file] = extraction.extracted_files
    assert extracted_file.format is None
    with subtests.test("delete file should also delete extractions"):
        await file.delete()

    with (
        subtests.test("verify file deleted"),
        pytest.raises(httpx.HTTPStatusError, match="404 Not Found"),
    ):
        async with file.load_content():
            ...


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
            pytest.raises(httpx.HTTPStatusError, match=r"404 Not Found|403 Forbidden"),
        ):
            await File.get(file_id_1, client=client_2)

        with (
            subtests.test("cannot access context 1 file content using context 2 client"),
            pytest.raises(httpx.HTTPStatusError, match=r"404 Not Found|403 Forbidden"),
        ):
            async with File.load_content(file_id_1, client=client_2):
                ...

        # Verify file cannot be deleted from different context using wrong client
        with (
            subtests.test("cannot delete context 1 file using context 2 client"),
            pytest.raises(httpx.HTTPStatusError, match=r"404 Not Found|403 Forbidden"),
        ):
            await File.delete(file_id_1, client=client_2)

        # Verify cross-context isolation works both ways
        with (
            subtests.test("cannot access context 2 file using context 1 client"),
            pytest.raises(httpx.HTTPStatusError, match=r"404 Not Found|403 Forbidden"),
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
            pytest.raises(httpx.HTTPStatusError, match=r"404 Not Found|403 Forbidden"),
        ):
            await File.get_extraction(file_id, client=client_2)

        with (
            subtests.test("cannot access text content from context 2"),
            pytest.raises(httpx.HTTPStatusError, match=r"404 Not Found|403 Forbidden"),
        ):
            async with File.load_text_content(file_id, client=client_2):
                ...

        # Verify extraction cannot be created from wrong context
        with (
            subtests.test("cannot create extraction from context 2"),
            pytest.raises(httpx.HTTPStatusError, match=r"404 Not Found|403 Forbidden"),
        ):
            await File.create_extraction(file_id, client=client_2)

        # Verify extraction cannot be deleted from wrong context
        with (
            subtests.test("cannot delete extraction from context 2"),
            pytest.raises(httpx.HTTPStatusError, match=r"404 Not Found|403 Forbidden"),
        ):
            await File.delete_extraction(file_id, client=client_2)

        # Clean up
        with subtests.test("clean up - delete extraction"):
            await File.delete_extraction(file_id, client=client_1)

        with subtests.test("clean up - delete file"):
            await File.delete(file_id, client=client_1)


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_files_list(subtests):
    """Test listing files with various filters and pagination"""

    # Create multiple test files with different attributes
    with subtests.test("create test files"):
        file1 = await File.create(
            filename="test_alpha.txt",
            content=b"content alpha",
            content_type="text/plain",
        )
        file2 = await File.create(
            filename="test_beta.json",
            content=b'{"key": "value"}',
            content_type="application/json",
        )
        file3 = await File.create(
            filename="test_gamma.txt",
            content=b"content gamma",
            content_type="text/plain",
        )
        file4 = await File.create(
            filename="production_data.csv",
            content=b"col1,col2\nval1,val2",
            content_type="text/csv",
        )

    with subtests.test("list all files"):
        result = await File.list()
        assert len(result.items) >= 4
        file_ids = {f.id for f in result.items}
        assert file1.id in file_ids
        assert file2.id in file_ids
        assert file3.id in file_ids
        assert file4.id in file_ids

    with subtests.test("filter by filename_search"):
        result = await File.list(filename_search="test_")
        assert len(result.items) >= 3
        for file in result.items:
            assert "test_" in file.filename.lower()
        # Verify file4 is not in the results
        file_ids = {f.id for f in result.items}
        assert file4.id not in file_ids

    with subtests.test("filter by content_type - text/plain"):
        result = await File.list(content_type="text/plain")
        assert len(result.items) >= 2
        for file in result.items:
            assert file.content_type == "text/plain"
        # Verify json file is not in the results
        file_ids = {f.id for f in result.items}
        assert file2.id not in file_ids

    with subtests.test("filter by content_type - application/json"):
        result = await File.list(content_type="application/json")
        assert len(result.items) >= 1
        file_ids = {f.id for f in result.items}
        assert file2.id in file_ids
        for file in result.items:
            assert file.content_type == "application/json"

    with subtests.test("pagination with limit"):
        result = await File.list(limit=2)
        assert len(result.items) <= 2
        assert result.next_page_token is not None or len(result.items) < 2

    with subtests.test("pagination with page_token"):
        first_page = await File.list(limit=2)
        if first_page.next_page_token:
            second_page = await File.list(limit=2, page_token=first_page.next_page_token)
            # Verify pages contain different items
            first_page_ids = {f.id for f in first_page.items}
            second_page_ids = {f.id for f in second_page.items}
            assert first_page_ids.isdisjoint(second_page_ids)

    with subtests.test("order by filename ascending"):
        result = await File.list(
            filename_search="test_",
            order="asc",
            order_by="filename",
        )
        filenames = [f.filename for f in result.items]
        assert filenames == ["test_alpha.txt", "test_beta.json", "test_gamma.txt"]

    with subtests.test("order by filename descending"):
        result = await File.list(
            filename_search="test_",
            order="desc",
            order_by="filename",
        )
        filenames = [f.filename for f in result.items]
        assert filenames == ["test_gamma.txt", "test_beta.json", "test_alpha.txt"]

    with subtests.test("order by created_at ascending"):
        result = await File.list(
            filename_search="test_",
            order="asc",
            order_by="created_at",
        )
        # Files were created in order: file1, file2, file3
        filenames = [f.filename for f in result.items]
        assert filenames == ["test_alpha.txt", "test_beta.json", "test_gamma.txt"]

    with subtests.test("order by created_at descending"):
        result = await File.list(
            filename_search="test_",
            order="desc",
            order_by="created_at",
        )
        # Files were created in order: file3, file2, file1
        filenames = [f.filename for f in result.items]
        assert filenames == ["test_gamma.txt", "test_beta.json", "test_alpha.txt"]

    with subtests.test("order by file_size_bytes descending"):
        result = await File.list(
            filename_search="test_",
            order="desc",
            order_by="file_size_bytes",
        )
        # Sizes: test_alpha.txt=13, test_beta.json=16, test_gamma.txt=13
        filenames = [f.filename for f in result.items]
        # test_beta.json (16 bytes) should be first, then the 13-byte files
        assert filenames[0] == "test_beta.json"
        assert set(filenames[1:]) == {"test_alpha.txt", "test_gamma.txt"}

    with subtests.test("filter by context_id"):
        # Create two contexts
        ctx1 = await Context.create()
        ctx2 = await Context.create()

        # Generate context tokens
        permissions = ContextPermissions(files={"read", "write"})
        token_1 = await ctx1.generate_token(grant_context_permissions=permissions)
        token_2 = await ctx2.generate_token(grant_context_permissions=permissions)

        # Create platform clients with context tokens
        async with (
            PlatformClient(context_id=ctx1.id, auth_token=token_1.token.get_secret_value()) as client_1,
            PlatformClient(context_id=ctx2.id, auth_token=token_2.token.get_secret_value()) as client_2,
        ):
            # Upload files in different contexts
            ctx1_file1 = await File.create(
                filename="ctx1_file1.txt",
                content=b"context 1 file 1",
                content_type="text/plain",
                client=client_1,
            )
            ctx1_file2 = await File.create(
                filename="ctx1_file2.txt",
                content=b"context 1 file 2",
                content_type="text/plain",
                client=client_1,
            )
            ctx2_file1 = await File.create(
                filename="ctx2_file1.txt",
                content=b"context 2 file 1",
                content_type="text/plain",
                client=client_2,
            )

            # List files for context 1 using client_1
            result = await File.list(client=client_1)
            file_ids = {f.id for f in result.items}
            assert ctx1_file1.id in file_ids
            assert ctx1_file2.id in file_ids
            assert ctx2_file1.id not in file_ids

            # List files for context 2 using client_2
            result = await File.list(client=client_2)
            file_ids = {f.id for f in result.items}
            assert ctx2_file1.id in file_ids
            assert ctx1_file1.id not in file_ids
            assert ctx1_file2.id not in file_ids

    with subtests.test("combine multiple filters"):
        result = await File.list(
            filename_search="test_",
            content_type="text/plain",
            order="asc",
            order_by="filename",
        )
        # Should get both text/plain files that match "test_" in alphabetical order
        filenames = [f.filename for f in result.items]
        assert filenames == ["test_alpha.txt", "test_gamma.txt"]
        for file in result.items:
            assert file.content_type == "text/plain"


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_files_list_user_global_and_context_scoped(subtests):
    """Test listing all user files (global) vs context-scoped files"""

    # Create files without context (global user files)
    with subtests.test("create global user files (no context)"):
        global_file1 = await File.create(
            filename="global_file1.txt",
            content=b"global content 1",
            content_type="text/plain",
            context_id=None,
        )
        global_file2 = await File.create(
            filename="global_file2.txt",
            content=b"global content 2",
            content_type="text/plain",
            context_id=None,
        )

    # Create contexts and files within them
    with subtests.test("create contexts"):
        ctx1 = await Context.create()
        ctx2 = await Context.create()

    with subtests.test("generate context tokens"):
        permissions = ContextPermissions(files={"read", "write"})
        token_1 = await ctx1.generate_token(grant_context_permissions=permissions)
        token_2 = await ctx2.generate_token(grant_context_permissions=permissions)

    async with (
        PlatformClient(context_id=ctx1.id, auth_token=token_1.token.get_secret_value()) as client_1,
        PlatformClient(context_id=ctx2.id, auth_token=token_2.token.get_secret_value()) as client_2,
    ):
        with subtests.test("create files in context 1"):
            ctx1_file1 = await File.create(
                filename="ctx1_file1.txt",
                content=b"context 1 content 1",
                content_type="text/plain",
                client=client_1,
            )
            ctx1_file2 = await File.create(
                filename="ctx1_file2.txt",
                content=b"context 1 content 2",
                content_type="text/plain",
                client=client_1,
            )

        with subtests.test("create files in context 2"):
            ctx2_file1 = await File.create(
                filename="ctx2_file1.txt",
                content=b"context 2 content 1",
                content_type="text/plain",
                client=client_2,
            )

        # List all files for the user (no context filter)
        with subtests.test("list all user files (context_id=None)"):
            result = await File.list(context_id=None)
            file_ids = {f.id for f in result.items}

            # Should contain all files: global and context-scoped
            assert global_file1.id in file_ids, "Global file 1 should be in results"
            assert global_file2.id in file_ids, "Global file 2 should be in results"
            assert ctx1_file1.id in file_ids, "Context 1 file 1 should be in results"
            assert ctx1_file2.id in file_ids, "Context 1 file 2 should be in results"
            assert ctx2_file1.id in file_ids, "Context 2 file 1 should be in results"

        # List files within context 1 only
        with subtests.test("list files in context 1 only"):
            result = await File.list(client=client_1)
            file_ids = {f.id for f in result.items}

            # Should only contain context 1 files
            assert ctx1_file1.id in file_ids, "Context 1 file 1 should be in results"
            assert ctx1_file2.id in file_ids, "Context 1 file 2 should be in results"

            # Should NOT contain global or context 2 files
            assert global_file1.id not in file_ids, "Global file 1 should NOT be in context 1 results"
            assert global_file2.id not in file_ids, "Global file 2 should NOT be in context 1 results"
            assert ctx2_file1.id not in file_ids, "Context 2 file 1 should NOT be in context 1 results"

        # List files within context 2 only
        with subtests.test("list files in context 2 only"):
            result = await File.list(client=client_2)
            file_ids = {f.id for f in result.items}

            # Should only contain context 2 files
            assert ctx2_file1.id in file_ids, "Context 2 file 1 should be in results"

            # Should NOT contain global or context 1 files
            assert global_file1.id not in file_ids, "Global file 1 should NOT be in context 2 results"
            assert global_file2.id not in file_ids, "Global file 2 should NOT be in context 2 results"
            assert ctx1_file1.id not in file_ids, "Context 1 file 1 should NOT be in context 2 results"
            assert ctx1_file2.id not in file_ids, "Context 1 file 2 should NOT be in context 2 results"

        # List all user files with filename filter
        with subtests.test("list all user files with filename filter"):
            result = await File.list(
                filename_search="global_",
                context_id=None,
            )
            file_ids = {f.id for f in result.items}

            # Should only contain global files matching the filter
            assert global_file1.id in file_ids
            assert global_file2.id in file_ids
            assert ctx1_file1.id not in file_ids
            assert ctx2_file1.id not in file_ids

        # List all user files ordered by filename desc
        with subtests.test("list all user files ordered by filename desc"):
            result = await File.list(
                context_id=None,
                order="desc",
                order_by="filename",
            )
            filenames = [f.filename for f in result.items]

            # Verify files are ordered alphabetically descending
            expected_order = sorted(
                ["global_file1.txt", "global_file2.txt", "ctx1_file1.txt", "ctx1_file2.txt", "ctx2_file1.txt"],
                reverse=True,
            )
            # Filter to only our test files
            test_filenames = [f for f in filenames if f in expected_order]
            assert test_filenames == expected_order


@pytest.mark.usefixtures("clean_up")
async def test_files_list_user_isolation(subtests, test_configuration):
    """Test that users cannot see files uploaded by other users when listing files.

    This test verifies user-level data isolation - each user should only see their own files,
    not files uploaded by other users.

    NOTE: This test requires basic auth to be enabled to distinguish between users!
    """
    base_url = test_configuration.server_url

    # Use admin user and regular user to test isolation
    # With basic auth enabled:
    # - correct admin password → admin@beeai.dev
    # - any other password → user@beeai.dev
    async with (
        AsyncClient(base_url=f"{base_url}/api/v1", auth=("admin", "test-password")) as admin_client,
        AsyncClient(base_url=f"{base_url}/api/v1", auth=("user", "not-admin")) as user_client,
    ):
        # Upload files as admin user
        with subtests.test("upload files as admin user"):
            admin_file1_response = await admin_client.post(
                "/files",
                files={"file": ("admin_file1.txt", b"admin content 1", "text/plain")},
            )
            assert admin_file1_response.status_code == 201
            admin_file1_id = admin_file1_response.json()["id"]

            admin_file2_response = await admin_client.post(
                "/files",
                files={"file": ("admin_file2.txt", b"admin content 2", "text/plain")},
            )
            assert admin_file2_response.status_code == 201
            admin_file2_id = admin_file2_response.json()["id"]

        # Upload files as regular user
        with subtests.test("upload files as regular user"):
            user_file1_response = await user_client.post(
                "/files",
                files={"file": ("user_file1.txt", b"user content 1", "text/plain")},
            )
            assert user_file1_response.status_code == 201
            user_file1_id = user_file1_response.json()["id"]

            user_file2_response = await user_client.post(
                "/files",
                files={"file": ("user_file2.txt", b"user content 2", "text/plain")},
            )
            assert user_file2_response.status_code == 201
            user_file2_id = user_file2_response.json()["id"]

        # Admin user lists files - should only see admin's files
        with subtests.test("admin user lists files - should only see own files"):
            admin_list_response = await admin_client.get("/files")
            assert admin_list_response.status_code == 200
            admin_files = admin_list_response.json()
            admin_file_ids = {f["id"] for f in admin_files["items"]}

            # Admin should see their own files
            assert admin_file1_id in admin_file_ids, "Admin should see admin_file1"
            assert admin_file2_id in admin_file_ids, "Admin should see admin_file2"

            # Admin should NOT see regular user's files
            assert user_file1_id not in admin_file_ids, "Admin should NOT see user_file1"
            assert user_file2_id not in admin_file_ids, "Admin should NOT see user_file2"

        # Regular user lists files - should only see their own files
        with subtests.test("regular user lists files - should only see own files"):
            user_list_response = await user_client.get("/files")
            assert user_list_response.status_code == 200
            user_files = user_list_response.json()
            user_file_ids = {f["id"] for f in user_files["items"]}

            # Regular user should see their own files
            assert user_file1_id in user_file_ids, "Regular user should see user_file1"
            assert user_file2_id in user_file_ids, "Regular user should see user_file2"

            # Regular user should NOT see admin's files
            assert admin_file1_id not in user_file_ids, "Regular user should NOT see admin_file1"
            assert admin_file2_id not in user_file_ids, "Regular user should NOT see admin_file2"

        # Verify filtering still works within user scope
        with subtests.test("admin user filters by filename - only sees own matching files"):
            admin_filtered_response = await admin_client.get("/files", params={"filename_search": "admin_"})
            assert admin_filtered_response.status_code == 200
            filtered_files = admin_filtered_response.json()
            filtered_ids = {f["id"] for f in filtered_files["items"]}

            # Should see admin files matching filter
            assert admin_file1_id in filtered_ids
            assert admin_file2_id in filtered_ids
            # Should not see user files (even if they matched the filter pattern)
            assert user_file1_id not in filtered_ids
            assert user_file2_id not in filtered_ids

        # Clean up - delete files
        with subtests.test("clean up - delete admin files"):
            await admin_client.delete(f"/files/{admin_file1_id}")
            await admin_client.delete(f"/files/{admin_file2_id}")

        with subtests.test("clean up - delete user files"):
            await user_client.delete(f"/files/{user_file1_id}")
            await user_client.delete(f"/files/{user_file2_id}")
