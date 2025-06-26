# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator
from uuid import UUID

import aioboto3
from botocore.exceptions import ClientError
from kink import inject

from beeai_server.configuration import Configuration
from beeai_server.domain.models.file import AsyncFile
from beeai_server.domain.repositories.files import IObjectStorageRepository
from beeai_server.exceptions import EntityNotFoundError

logger = logging.getLogger(__name__)


@inject
class S3ObjectStorageRepository(IObjectStorageRepository):
    """Implementation of IObjectStorageRepository using S3-compatible storage."""

    def __init__(self, configuration: Configuration):
        self.config = configuration.object_storage

    def _get_client(self):
        session = aioboto3.Session()
        return session.client(
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
                    raise EntityNotFoundError(entity="file", id=file_id)
                raise

    async def delete_file(self, *, file_id: UUID) -> None:
        object_key = self._get_object_key(file_id)

        async with self._get_client() as client:
            try:
                await client.delete_object(Bucket=self.config.bucket_name, Key=object_key)
            except ClientError as e:
                logger.error(f"Error deleting file {file_id}: {e}")
                raise

    async def get_file_url(self, *, file_id: UUID) -> str:
        object_key = self._get_object_key(file_id)
        async with self._get_client() as client:
            try:
                await client.head_object(Bucket=self.config.bucket_name, Key=object_key)
                url = await client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.config.bucket_name, "Key": object_key},
                    ExpiresIn=3600,  # 1 hour
                )
                return url

            except ClientError as e:
                if e.response["Error"]["Code"] == "NoSuchKey" or e.response["Error"]["Code"] == "404":
                    raise EntityNotFoundError(entity="file", id=file_id)
                raise
