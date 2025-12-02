# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncIterator

import pytest

from agentstack_server.domain.models.file import AsyncFile

pytestmark = pytest.mark.unit


async def mock_iterator() -> AsyncIterator[bytes]:
    yield b"hello"
    yield b" "
    yield b"world"
    yield b"!"


@pytest.mark.asyncio
async def test_async_file_read_chunking():
    """Test that AsyncFile.from_async_iterator correctly chunks data."""
    af = AsyncFile.from_async_iterator(mock_iterator(), "test.txt", "text/plain")

    # Read 3 bytes
    chunk1 = await af.read(3)
    assert chunk1 == b"hel"

    # Read 3 bytes (should get 'lo ')
    chunk2 = await af.read(3)
    assert chunk2 == b"lo "

    # Read rest (larger than remaining)
    chunk3 = await af.read(100)
    assert chunk3 == b"world!"

    # Read EOF
    chunk4 = await af.read(100)
    assert chunk4 == b""


@pytest.mark.asyncio
async def test_async_file_read_exact_size():
    """Test AsyncFile.from_async_iterator reading exact size of chunks."""

    async def iterator() -> AsyncIterator[bytes]:
        yield b"123456"

    af = AsyncFile.from_async_iterator(iterator(), "test.txt", "text/plain")

    chunk1 = await af.read(3)
    assert chunk1 == b"123"

    chunk2 = await af.read(3)
    assert chunk2 == b"456"

    chunk3 = await af.read(3)
    assert chunk3 == b""


@pytest.mark.asyncio
async def test_async_file_read_across_chunks():
    """Test AsyncFile.from_async_iterator reading spanning multiple chunks."""

    async def iterator() -> AsyncIterator[bytes]:
        yield b"ab"
        yield b"cd"
        yield b"ef"

    af = AsyncFile.from_async_iterator(iterator(), "test.txt", "text/plain")

    # Read 3 bytes (ab + c)
    chunk1 = await af.read(3)
    assert chunk1 == b"abc"

    # Read 3 bytes (d + ef)
    chunk2 = await af.read(3)
    assert chunk2 == b"def"


@pytest.mark.asyncio
async def test_async_file_from_content():
    """Test AsyncFile.from_content."""
    content = b"hello world from buffer"
    af = AsyncFile.from_bytes(content, "mem_test.txt", "text/plain")

    assert af.size == len(content)

    # Read 5 bytes
    chunk1 = await af.read(5)
    assert chunk1 == b"hello"

    # Read 6 bytes
    chunk2 = await af.read(6)
    assert chunk2 == b" world"

    # Read 100 bytes (remaining)
    chunk3 = await af.read(100)
    assert chunk3 == b" from buffer"

    # Read EOF
    chunk4 = await af.read(100)
    assert chunk4 == b""


@pytest.mark.asyncio
async def test_async_file_from_content_exact_chunks():
    """Test AsyncFile.from_content with exact chunk sizes."""
    content = b"123456"
    af = AsyncFile.from_bytes(content, "mem_test.txt", "text/plain")

    chunk1 = await af.read(3)
    assert chunk1 == b"123"

    chunk2 = await af.read(3)
    assert chunk2 == b"456"

    chunk3 = await af.read(3)
    assert chunk3 == b""
