# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import Any
from uuid import UUID

import aioboto3
import aioboto3.s3.inject
from botocore.exceptions import ClientError
from kink import inject
from pydantic import HttpUrl

from agentstack_server.configuration import Configuration
from agentstack_server.domain.models.file import AsyncFile, FileMetadata
from agentstack_server.domain.repositories.file import IObjectStorageRepository
from agentstack_server.exceptions import EntityNotFoundError

logger = logging.getLogger(__name__)


@inject
class S3ObjectStorageRepository(IObjectStorageRepository):
    """Implementation of IObjectStorageRepository using S3-compatible storage."""

    def __init__(self, configuration: Configuration):
        self.config = configuration.object_storage

    def _get_client(self) -> AbstractAsyncContextManager[Any]:
        session = aioboto3.Session()
        return session.client(  # pyright: ignore [reportReturnType]
            "s3",
            endpoint_url=str(self.config.endpoint_url),
            aws_access_key_id=self.config.access_key_id.get_secret_value(),
            aws_secret_access_key=self.config.access_key_secret.get_secret_value(),
            region_name=self.config.region,
            use_ssl=self.config.use_ssl,
        )

    def _get_object_key(self, file_id: UUID) -> str:
        return f"files/{file_id}"

    async def upload_file(self, *, file_id: UUID, file: AsyncFile) -> int:
        object_key = self._get_object_key(file_id)
        async with self._get_client() as client:
            await client.upload_fileobj(
                file,
                self.config.bucket_name,
                object_key,
                ExtraArgs={"ContentType": file.content_type, "Metadata": {"filename": file.filename}},
            )
            result = await client.head_object(Bucket=self.config.bucket_name, Key=object_key)
            return result["ContentLength"]

    @asynccontextmanager
    async def get_file(self, *, file_id: UUID) -> AsyncIterator[AsyncFile]:
        object_key = self._get_object_key(file_id)
        async with self._get_client() as client:
            try:
                response = await client.get_object(Bucket=self.config.bucket_name, Key=object_key)

                async def read(amount: int = 8192) -> bytes:
                    return await response["Body"].read(amount)

                yield AsyncFile(
                    filename=response["Metadata"]["filename"], content_type=response["ContentType"], read=read
                )

            except ClientError as e:
                if e.response["Error"]["Code"] == "NoSuchKey":
                    raise EntityNotFoundError(entity="file", id=file_id) from e
                raise

    async def delete_files(self, *, file_ids: list[UUID]) -> None:
        if not file_ids:
            return

        async with self._get_client() as client:
            # S3 delete_objects supports up to 1000 objects per request
            chunk_size = 1000
            for i in range(0, len(file_ids), chunk_size):
                chunk = file_ids[i : i + chunk_size]
                objects_to_delete = [{"Key": self._get_object_key(file_id)} for file_id in chunk]

                try:
                    response = await client.delete_objects(
                        Bucket=self.config.bucket_name, Delete={"Objects": objects_to_delete}
                    )

                    # Raise if there are any errors from the bulk delete
                    if response.get("Errors"):
                        error_messages = [f"{error['Key']}: {error['Message']}" for error in response["Errors"]]
                        raise RuntimeError(f"Failed to delete some files: {'; '.join(error_messages)}")

                except ClientError as e:
                    logger.error(f"Error bulk deleting files: {e}")
                    raise

    async def get_file_url(self, *, file_id: UUID) -> HttpUrl:
        object_key = self._get_object_key(file_id)
        async with self._get_client() as client:
            try:
                await client.head_object(Bucket=self.config.bucket_name, Key=object_key)
                url = await client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.config.bucket_name, "Key": object_key},
                    ExpiresIn=3600,  # 1 hour
                )
                return HttpUrl(url)

            except ClientError as e:
                if e.response["Error"]["Code"] == "NoSuchKey" or e.response["Error"]["Code"] == "404":
                    raise EntityNotFoundError(entity="file", id=file_id) from e
                raise

    async def get_file_metadata(self, *, file_id: UUID) -> FileMetadata:
        object_key = self._get_object_key(file_id)
        async with self._get_client() as client:
            try:
                response = await client.head_object(Bucket=self.config.bucket_name, Key=object_key)
                return FileMetadata(
                    content_type=response.get("ContentType", ""),
                    filename=response.get("Metadata", {}).get("filename", ""),
                    content_length=response.get("ContentLength", 0),
                )
            except ClientError as e:
                if e.response["Error"]["Code"] == "NoSuchKey" or e.response["Error"]["Code"] == "404":
                    raise EntityNotFoundError(entity="file", id=file_id) from e
                raise
