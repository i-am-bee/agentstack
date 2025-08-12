# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncIterator
from typing import cast
from uuid import UUID

from kink import inject
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Row,
    String,
    Table,
    Text,
    func,
    select,
)
from sqlalchemy import UUID as SQL_UUID
from sqlalchemy.ext.asyncio import AsyncConnection

from beeai_server.domain.models.file import ExtractionStatus, File, FileType, TextExtraction
from beeai_server.domain.repositories.file import IFileRepository
from beeai_server.exceptions import EntityNotFoundError
from beeai_server.infrastructure.persistence.repositories.db_metadata import metadata

files_table = Table(
    "files",
    metadata,
    Column("id", SQL_UUID, primary_key=True),
    Column("filename", String(256), nullable=False),
    Column("file_size_bytes", Integer, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("created_by", ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("file_type", Enum(FileType, name="file_type"), nullable=False),
    Column("parent_file_id", ForeignKey("files.id", ondelete="CASCADE"), nullable=True),
    Column("context_id", ForeignKey("contexts.id", ondelete="CASCADE"), nullable=True),
)

text_extractions_table = Table(
    "text_extractions",
    metadata,
    Column("id", SQL_UUID, primary_key=True),
    Column("file_id", ForeignKey("files.id", ondelete="CASCADE"), nullable=False, unique=True),
    Column("extracted_file_id", ForeignKey("files.id", ondelete="SET NULL"), nullable=True),
    Column("status", Enum(ExtractionStatus, name="extraction_status"), nullable=False),
    Column("job_id", String(255), nullable=True),
    Column("error_message", Text, nullable=True),
    Column("extraction_metadata", JSON, nullable=True),
    Column("started_at", DateTime(timezone=True), nullable=True),
    Column("finished_at", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
)


@inject
class SqlAlchemyFileRepository(IFileRepository):
    def __init__(self, connection: AsyncConnection):
        self.connection = connection

    async def create(self, *, file: File) -> None:
        query = files_table.insert().values(
            id=file.id,
            filename=file.filename,
            created_at=file.created_at,
            created_by=file.created_by,
            file_size_bytes=file.file_size_bytes,
            file_type=file.file_type,
            parent_file_id=file.parent_file_id,
            context_id=file.context_id,
        )
        await self.connection.execute(query)

    def _to_file(self, row: Row):
        return File.model_validate(
            {
                "id": row.id,
                "filename": row.filename,
                "created_at": row.created_at,
                "created_by": row.created_by,
                "file_size_bytes": row.file_size_bytes,
                "file_type": row.file_type,
                "parent_file_id": row.parent_file_id,
                "context_id": row.context_id,
            }
        )

    async def total_usage(self, *, user_id: UUID | None = None) -> int:
        query = select(func.coalesce(func.sum(files_table.c.file_size_bytes), 0))
        if user_id:
            query = query.where(files_table.c.created_by == user_id)
        return cast(int, await self.connection.scalar(query))

    async def get(
        self,
        *,
        file_id: UUID,
        user_id: UUID | None = None,
        context_id: UUID | None = None,
        file_type: FileType | None = None,
    ) -> File:
        query = files_table.select().where(files_table.c.id == file_id)
        if user_id:
            query = query.where(files_table.c.created_by == user_id)
        if context_id:
            query = query.where(files_table.c.context_id == context_id)
        if file_type:
            query = query.where(files_table.c.file_type == file_type)
        result = await self.connection.execute(query)
        if not (row := result.fetchone()):
            raise EntityNotFoundError(entity="file", id=file_id)
        return self._to_file(row)

    async def delete(
        self, *, file_id: UUID | None = None, user_id: UUID | None = None, context_id: UUID | None = None
    ) -> int:
        query = files_table.delete()

        conditions = []
        if file_id is not None:
            conditions.append(files_table.c.id == file_id)
        if context_id is not None:
            conditions.append(files_table.c.context_id == context_id)
        if user_id is not None:
            conditions.append(files_table.c.created_by == user_id)

        if not conditions:
            raise ValueError("At least one filter parameter must be provided")

        for condition in conditions:
            query = query.where(condition)
        result = await self.connection.execute(query)
        if not result.rowcount:
            raise EntityNotFoundError("file", file_id or "file to delete")
        return result.rowcount

    async def list(self, *, user_id: UUID | None = None, context_id: UUID | None = None) -> AsyncIterator[File]:
        query = files_table.select().where(files_table.c.file_type == FileType.user_upload)
        if user_id:
            query = query.where(files_table.c.created_by == user_id)
        if context_id:
            query = query.where(files_table.c.context_id == context_id)
        async for row in await self.connection.stream(query):
            yield self._to_file(row)

    def _to_text_extraction(self, row: Row) -> TextExtraction:
        return TextExtraction.model_validate(
            {
                "id": row.id,
                "file_id": row.file_id,
                "extracted_file_id": row.extracted_file_id,
                "status": row.status,
                "job_id": row.job_id,
                "error_message": row.error_message,
                "extraction_metadata": row.extraction_metadata,
                "started_at": row.started_at,
                "finished_at": row.finished_at,
                "created_at": row.created_at,
            }
        )

    async def create_extraction(self, *, extraction: TextExtraction) -> None:
        extraction_metadata = extraction.extraction_metadata
        query = text_extractions_table.insert().values(
            id=extraction.id,
            file_id=extraction.file_id,
            extracted_file_id=extraction.extracted_file_id,
            status=extraction.status,
            job_id=extraction.job_id,
            error_message=extraction.error_message,
            extraction_metadata=extraction_metadata and extraction_metadata.model_dump(mode="json"),
            started_at=extraction.started_at,
            finished_at=extraction.finished_at,
            created_at=extraction.created_at,
        )
        await self.connection.execute(query)

    async def get_extraction_by_file_id(
        self, *, file_id: UUID, user_id: UUID | None = None, context_id: UUID | None = None
    ) -> TextExtraction:
        query = text_extractions_table.select().where(text_extractions_table.c.file_id == file_id)
        if context_id or user_id:
            query = query.join(files_table, text_extractions_table.c.file_id == files_table.c.id)
        if context_id:
            query = query.where(files_table.c.context_id == context_id)
        if user_id:
            query = query.where(files_table.c.created_by == user_id)

        result = await self.connection.execute(query)
        if not (row := result.fetchone()):
            raise EntityNotFoundError(entity="text_extraction", id=file_id, attribute="file_id")
        return self._to_text_extraction(row)

    async def update_extraction(self, *, extraction: TextExtraction) -> None:
        query = (
            text_extractions_table.update()
            .where(text_extractions_table.c.file_id == extraction.file_id)
            .values(
                extracted_file_id=extraction.extracted_file_id,
                status=extraction.status,
                job_id=extraction.job_id,
                error_message=extraction.error_message,
                extraction_metadata=extraction.extraction_metadata,
                started_at=extraction.started_at,
                finished_at=extraction.finished_at,
            )
        )
        await self.connection.execute(query)

    async def delete_extraction(self, *, extraction_id: UUID) -> int:
        query = text_extractions_table.delete().where(text_extractions_table.c.id == extraction_id)
        result = await self.connection.execute(query)
        if not result.rowcount:
            raise EntityNotFoundError(entity="text_extraction", id=extraction_id)
        return result.rowcount
