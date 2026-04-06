# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import httpx
import pydantic
from pydantic import BaseModel

from agentstack_sdk.a2a.extensions.base import (
    BaseExtensionClient,
    BaseExtensionServer,
    NoParamsBaseExtensionSpec,
)
from agentstack_sdk.a2a.extensions.exceptions import ExtensionError

__all__ = [
    "S3_EXTENSION_URI",
    "S3Config",
    "S3ExtensionClient",
    "S3ExtensionMetadata",
    "S3ExtensionServer",
    "S3ExtensionSpec",
    "S3UploadSlot",
]

S3_EXTENSION_URI = "https://a2a-extensions.agentstack.beeai.dev/storage/s3/v1"


class S3UploadSlot(BaseModel):
    """Pre-signed URLs for one upload slot."""

    upload_url: str
    """Short-lived presigned PUT URL."""

    download_url: str
    """Short-lived presigned GET URL for the same key."""


class S3ExtensionMetadata(BaseModel):
    """Passed in message.metadata[S3_EXTENSION_URI]"""

    upload_slots: dict[str, S3UploadSlot] = {}
    """Keyed by slot name (e.g. "result")."""


class S3ExtensionSpec(NoParamsBaseExtensionSpec):
    URI = S3_EXTENSION_URI


class S3ExtensionServer(BaseExtensionServer[S3ExtensionSpec, S3ExtensionMetadata]):
    """
    Provides file upload/download to agents via pre-signed URLs.
    No S3 credentials required — URLs are injected by the client/platform.
    """

    async def upload(self, slot: str, content: bytes, content_type: str = "application/octet-stream") -> str:
        """Upload content to the named slot's presigned PUT URL. Returns the presigned download URL."""
        if not self.data:
            raise ExtensionError(self.spec, "S3 extension metadata was not provided")
        if slot not in self.data.upload_slots:
            raise ExtensionError(self.spec, f"Upload slot '{slot}' not found in S3 extension metadata")

        upload_slot = self.data.upload_slots[slot]
        async with httpx.AsyncClient() as http:
            resp = await http.put(
                upload_slot.upload_url,
                content=content,
                headers={"Content-Type": content_type},
            )
            resp.raise_for_status()
        return upload_slot.download_url

    async def download(self, url: str) -> bytes:
        """Download content from a presigned GET URL."""
        async with httpx.AsyncClient() as http:
            resp = await http.get(url)
            resp.raise_for_status()
            return resp.content


class S3Config(pydantic.BaseModel):
    """S3-compatible storage connection configuration."""

    endpoint_url: str
    bucket: str
    access_key: pydantic.SecretStr
    secret_key: pydantic.SecretStr
    region: str = "us-east-1"
    use_ssl: bool = False


class S3ExtensionClient(BaseExtensionClient[S3ExtensionSpec, None]):
    """
    Generates pre-signed upload/download URL pairs, scoped to context + user.
    Used by the client/platform — requires S3 credentials.
    """

    def __init__(self, config: S3Config, spec: S3ExtensionSpec | None = None) -> None:
        super().__init__(spec or S3ExtensionSpec())
        self._config = config

    async def create_upload_slot(
        self,
        *,
        slot: str,  # kept for naming clarity at call site, not used in URL generation
        context_id: str,
        user_id: str,
        filename: str,
        ttl: int = 3600,
    ) -> S3UploadSlot:
        """Generate a pair of presigned URLs for a specific upload slot, scoped to context + user."""
        try:
            import aioboto3
        except ImportError as e:
            raise ImportError(
                "aioboto3 is required for S3ExtensionClient. Install it with: pip install 'agentstack-sdk[s3]'"
            ) from e

        from botocore.config import Config
        from botocore.exceptions import ClientError

        key = f"{context_id}/{user_id}/{filename}"
        session = aioboto3.Session()
        async with session.client(
            "s3",
            endpoint_url=self._config.endpoint_url,
            aws_access_key_id=self._config.access_key.get_secret_value(),
            aws_secret_access_key=self._config.secret_key.get_secret_value(),
            region_name=self._config.region,
            use_ssl=self._config.use_ssl,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        ) as s3:
            try:
                await s3.head_bucket(Bucket=self._config.bucket)
            except ClientError as e:
                if e.response["Error"]["Code"] in ("404", "NoSuchBucket"):
                    await s3.create_bucket(Bucket=self._config.bucket)
                else:
                    raise

            upload_url = await s3.generate_presigned_url(
                "put_object",
                Params={"Bucket": self._config.bucket, "Key": key},
                ExpiresIn=ttl,
            )
            download_url = await s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._config.bucket, "Key": key},
                ExpiresIn=ttl,
            )
        return S3UploadSlot(upload_url=upload_url, download_url=download_url)

    def metadata(self, slots: dict[str, S3UploadSlot]) -> dict:
        """Build message metadata dict containing pre-signed URLs for each slot."""
        return {S3_EXTENSION_URI: S3ExtensionMetadata(upload_slots=slots).model_dump(mode="json")}
