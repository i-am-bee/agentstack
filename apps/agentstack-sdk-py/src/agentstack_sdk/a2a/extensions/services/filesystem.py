# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

"""
FileSystem extension providing fsspec-compatible access to AgentStack Files API.

Uses PlatformApiExtensionServer as a dependency for authentication and client management.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

import pydantic
from fsspec import AbstractFileSystem
from fsspec.implementations.memory import MemoryFile

from agentstack_sdk.a2a.extensions.base import NoParamsBaseExtensionSpec
from agentstack_sdk.a2a.extensions.services.platform import PlatformApiExtensionServer
from agentstack_sdk.platform import File

if TYPE_CHECKING:
    pass


class AgentStackFileSystem(AbstractFileSystem):
    """
    An fsspec-compatible filesystem that wraps the AgentStack File API.

    Example usage:
        fs = AgentStackFileSystem(platform=platform_ext)
        with fs.open("/data/myfile.csv") as f:
            content = f.read()
    """

    protocol: ClassVar[str | tuple[str, ...]] = "agentstack"

    def __init__(
        self,
        platform: PlatformApiExtensionServer,
        prefix: str = "",
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self._platform = platform
        self._prefix = prefix.rstrip("/")

    def _normalize_path(self, path: str) -> str:
        """Normalize the path by adding prefix."""
        path = path.lstrip("/")
        return f"{self._prefix}/{path}" if self._prefix else path

    def _strip_prefix(self, filename: str) -> str:
        """Strip the prefix from a filename."""
        if self._prefix and filename.startswith(self._prefix):
            return filename[len(self._prefix) :].lstrip("/")
        return filename

    def _run_async(self, coro):
        """Run async code from sync context using the platform client."""
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                return executor.submit(asyncio.run, coro).result()
        return asyncio.run(coro)

    def _open(  # type: ignore[override]
        self,
        path: str,
        mode: str = "rb",
        block_size: int | None = None,
        autocommit: bool = True,
        cache_options: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AgentStackFile:
        return AgentStackFile(
            fs=self,
            path=self._normalize_path(path),
            mode=mode,
            autocommit=autocommit,
            platform=self._platform,
            **kwargs,
        )

    def ls(self, path: str = "", detail: bool = True, **kwargs: Any) -> list[dict[str, Any]] | list[str]:
        """List files matching a path prefix."""
        search = self._normalize_path(path) if path else self._prefix

        async def _ls():
            async with self._platform.use_client() as client:
                result = await File.list(
                    filename_search=search or None,
                    client=client,
                    context_id=self._platform.context_id,
                )
                if detail:
                    return [
                        {
                            "name": self._strip_prefix(f.filename),
                            "size": f.file_size_bytes,
                            "type": "file",
                            "created": f.created_at.isoformat() if f.created_at else None,
                            "content_type": f.content_type,
                        }
                        for f in result.items
                    ]
                return [self._strip_prefix(f.filename) for f in result.items]

        return self._run_async(_ls())

    def info(self, path: str, **kwargs: Any) -> dict[str, Any]:
        """Get information about a file."""
        normalized = self._normalize_path(path)

        async def _info():
            async with self._platform.use_client() as client:
                result = await File.list(filename_search=normalized, client=client, context_id=self._platform.context_id)
                for f in result.items:
                    if f.filename == normalized:
                        return {
                            "name": self._strip_prefix(f.filename),
                            "size": f.file_size_bytes,
                            "type": "file",
                            "created": f.created_at.isoformat() if f.created_at else None,
                            "content_type": f.content_type,
                        }
                raise FileNotFoundError(f"File not found: {path}")

        return self._run_async(_info())

    def rm(self, path: str, recursive: bool = False, maxdepth: int | None = None) -> None:
        """Remove a file."""
        normalized = self._normalize_path(path)

        async def _rm():
            async with self._platform.use_client() as client:
                result = await File.list(filename_search=normalized, client=client, context_id=self._platform.context_id)
                for f in result.items:
                    if f.filename == normalized:
                        await f.delete(client=client, context_id=self._platform.context_id)
                        return
                raise FileNotFoundError(f"File not found: {path}")

        self._run_async(_rm())

    def exists(self, path: str, **kwargs: Any) -> bool:
        """Check if a file exists."""
        try:
            self.info(path, **kwargs)
            return True
        except FileNotFoundError:
            return False


class AgentStackFile(MemoryFile):
    """File-like object for reading/writing files in AgentStack."""

    def __init__(
        self,
        fs: AgentStackFileSystem,
        path: str,
        mode: str = "rb",
        autocommit: bool = True,
        platform: PlatformApiExtensionServer | None = None,
        **kwargs: Any,
    ):
        self.path = path
        self._mode = mode
        self._autocommit = autocommit
        self._platform = platform
        self._agentstack_fs = fs  # Store reference for our use

        data = self._load_content() if "r" in mode else None
        super().__init__(fs=fs, path=path, data=data, **kwargs)

    def _load_content(self) -> bytes:
        """Load file content from AgentStack."""
        if not self._platform:
            raise RuntimeError("Platform extension not available")
        platform = self._platform

        async def _load():
            async with platform.use_client() as client:
                result = await File.list(filename_search=self.path, client=client, context_id=platform.context_id)
                for f in result.items:
                    if f.filename == self.path:
                        async with f.load_content(client=client, context_id=platform.context_id) as loaded:
                            return loaded.content
                raise FileNotFoundError(f"File not found: {self.path}")

        return self._agentstack_fs._run_async(_load())

    def commit(self) -> None:
        """Commit the file content to AgentStack."""
        if "w" not in self._mode and "a" not in self._mode:
            return
        if not self._platform:
            raise RuntimeError("Platform extension not available")
        platform = self._platform

        content = self.getvalue()

        async def _commit():
            async with platform.use_client() as client:
                ct = "text/plain" if self.path.endswith(".txt") else "text/csv" if self.path.endswith(".csv") else "application/json" if self.path.endswith(".json") else "application/octet-stream"
                await File.create(filename=self.path, content=content, content_type=ct, client=client, context_id=platform.context_id)

        self._agentstack_fs._run_async(_commit())

    def close(self) -> None:
        if self._autocommit and ("w" in self._mode or "a" in self._mode):
            self.commit()
        super().close()


# Extension classes


class FileSystemExtensionSpec(NoParamsBaseExtensionSpec):
    """Specification for the FileSystem extension."""

    URI: str = "https://a2a-extensions.agentstack.beeai.dev/services/filesystem/v1"
    DESCRIPTION: str | None = "Provides fsspec-compatible filesystem access to AgentStack Files API"


class FileSystemExtensionServer(pydantic.BaseModel):
    """
    Server-side implementation of the FileSystem extension.

    Uses PlatformApiExtensionServer for authentication and API access.

    Example:
        @server.agent(name="My Agent")
        async def my_agent(
            message: Message,
            context: RunContext,
            platform: Annotated[PlatformApiExtensionServer, PlatformApiExtensionSpec()],
        ):
            file_system = FileSystemExtensionServer(platform=platform)
            with file_system.open("/data/myfile.csv") as f:
                content = f.read()
            yield content
    """

    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    platform: PlatformApiExtensionServer
    prefix: str = ""
    _fs: AgentStackFileSystem | None = None

    @property
    def fs(self) -> AgentStackFileSystem:
        """Get the underlying filesystem instance."""
        if self._fs is None:
            self._fs = AgentStackFileSystem(platform=self.platform, prefix=self.prefix)
        return self._fs

    def open(self, path: str, mode: str = "rb", **kwargs: Any) -> Any:
        """Open a file for reading or writing."""
        return self.fs.open(path, mode=mode, **kwargs)

    def ls(self, path: str = "", detail: bool = True, **kwargs: Any) -> list[dict[str, Any]] | list[str]:
        """List files matching a path prefix."""
        return self.fs.ls(path, detail=detail, **kwargs)

    def info(self, path: str, **kwargs: Any) -> dict[str, Any]:
        """Get information about a file."""
        return self.fs.info(path, **kwargs)

    def rm(self, path: str, recursive: bool = False, **kwargs: Any) -> None:
        """Remove a file."""
        self.fs.rm(path, recursive=recursive, **kwargs)

    def exists(self, path: str, **kwargs: Any) -> bool:
        """Check if a file exists."""
        return self.fs.exists(path, **kwargs)


__all__ = [
    "AgentStackFile",
    "AgentStackFileSystem",
    "FileSystemExtensionServer",
    "FileSystemExtensionSpec",
]
