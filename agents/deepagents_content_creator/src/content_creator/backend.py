# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import re
from datetime import datetime
from typing import Literal

import wcmatch.glob as wcglob

from deepagents.backends.protocol import (
    BackendProtocol,
    WriteResult,
    EditResult,
    FileDownloadResponse,
    FileUploadResponse,
)
from deepagents.backends.utils import FileInfo, GrepMatch, format_content_with_line_numbers

from agentstack_sdk.platform import File


class AgentStackBackend(BackendProtocol):
    def __init__(self, prefix: str = ""):
        self.prefix = prefix.rstrip("/")

    def _key(self, path: str) -> str:
        return f"{self.prefix}{path}".lstrip("/")

    async def _find_by_name(self, path: str) -> File | None:
        key = self._key(path)
        result = await File.list(filename_search=key)
        return next((f for f in result.items if f.filename == key), None)

    async def alist(
        self,
        filename_search: str | None = None,
        order: Literal["asc"] | Literal["desc"] | None = "asc",
        order_by: Literal["created_at"] | Literal["filename"] | Literal["file_size_bytes"] | None = None,
        created_after: datetime | None = None,
    ) -> list[File]:
        filename_search = self._key(filename_search) if filename_search else None
        results = await File.list(filename_search=filename_search, order_by=order_by, order=order)
        return [file for file in results.items if created_after is None or file.created_at > created_after]

    async def als_info(self, path: str) -> list[FileInfo]:
        files = await self.alist(filename_search=path)
        return [
            FileInfo(
                path=file.filename[len(self.prefix) :]
                if self.prefix and file.filename.startswith(self.prefix)
                else file.filename,
                is_dir=False,
                size=file.file_size_bytes,
                modified_at=str(file.created_at),
            )
            for file in files
        ]

    async def aread(self, file_path: str, offset: int = 0, limit: int = 2000) -> str:
        file = await self._find_by_name(file_path)
        if not file:
            return f"Error: File '{file_path}' not found"

        if file.content_type.startswith("image") or file.content_type.startswith("application"):
            return f"Error: File '{file_path}' cannot be read because its content is not a text."

        async with file.load_text_content() as loaded_file:
            content = loaded_file.text
            lines = content.splitlines()
            start_idx = offset
            end_idx = min(start_idx + limit, len(lines))

            if start_idx >= len(lines):
                return f"Error: Line offset {offset} exceeds file length ({len(lines)} lines)"

            selected_lines = lines[start_idx:end_idx]
            return format_content_with_line_numbers(selected_lines, start_line=start_idx + 1)

    async def agrep_raw(self, pattern: str, path: str | None = None, glob: str | None = None) -> list[GrepMatch] | str:
        search_path = path or "/"
        file_infos = await self.aglob_info(glob or "**/*", search_path)

        matches: list[GrepMatch] = []
        for info in file_infos:
            file_path = info["path"]
            key = self._key(file_path)
            try:
                async with File.load_text_content(key) as loaded_file:
                    content = loaded_file.text
                    for i, line in enumerate(content.splitlines(), 1):
                        if pattern in line:
                            matches.append({"path": file_path, "line": i, "text": line})
            except Exception:
                continue
        return matches

    async def aglob_info(self, pattern: str, path: str = "/") -> list[FileInfo]:
        """Find files matching a glob pattern.

        Args:
            pattern: Glob pattern with wildcards to match file paths.
            path: Base directory to search from. Default: "/" (root).

        Returns:
            list of FileInfo
        """
        search_path = path.rstrip("/")
        prefix_key = self._key(search_path)

        # list all files starting with prefix
        result = await File.list(filename_search=prefix_key)

        matched_files: list[FileInfo] = []
        for file in result.items:
            file_full_path = file.filename
            if self.prefix and file_full_path.startswith(self.prefix):
                relative_path = file_full_path[len(self.prefix) :]
            else:
                relative_path = file_full_path

            # pattern is relative to 'path'
            # We need to check if relative_path matches path + pattern
            normalized_search_path = search_path if search_path.startswith("/") else "/" + search_path
            full_pattern = (normalized_search_path + "/" + pattern.lstrip("/")).lstrip("/")

            if wcglob.globmatch(relative_path.lstrip("/"), full_pattern, flags=wcglob.GLOBSTAR | wcglob.BRACE):
                matched_files.append(
                    FileInfo(
                        path=relative_path,
                        is_dir=False,
                        size=file.file_size_bytes,
                        modified_at=str(file.created_at),
                    )
                )

        return matched_files

    async def awrite(self, file_path: str, content: str) -> WriteResult:
        try:
            await File.create(filename=self._key(file_path), content=content.encode(), content_type="text/plain")
            return WriteResult(error=None, path=file_path, files_update=None)
        except Exception as e:
            return WriteResult(error=str(e), path=file_path, files_update=None)

    async def download_file(self, path: str) -> FileDownloadResponse:
        file = await self._find_by_name(path)
        if not file:
            return FileDownloadResponse(error="file_not_found", path=path)

        async with file.load_content() as loaded_file:
            return FileDownloadResponse(error=None, path=path, content=loaded_file.content)

    async def adownload_files(self, paths: list[str]) -> list[FileDownloadResponse]:
        files = await asyncio.gather(*(self.download_file(path) for path in paths))
        return list(files)

    async def upload_file(self, path: str, content: bytes) -> FileUploadResponse:
        await File.create(filename=self._key(path), content=content, content_type="application/octet-stream")
        return FileUploadResponse(error=None, path=path)

    async def aupload_files(self, files: list[tuple[str, bytes]]) -> list[FileUploadResponse]:
        files = await asyncio.gather(*(self.upload_file(path, content) for path, content in files))
        return list(files)

    async def aedit(self, file_path: str, old_string: str, new_string: str, replace_all: bool = False) -> EditResult:
        file = await self._find_by_name(file_path)
        if not file:
            return EditResult(error=f"File '{file_path}' not found")

        async with file.load_text_content() as loaded_file:
            current_data = loaded_file.text

        new_data, occurrences = re.subn(old_string, new_string, current_data, 0 if replace_all else 1)
        if not occurrences:
            return EditResult(error="No occurrences found", occurrences=0, path=file_path)

        await self.awrite(file_path, new_data)
        await file.delete()

        return EditResult(
            occurrences=occurrences,
            error=None,
        )
