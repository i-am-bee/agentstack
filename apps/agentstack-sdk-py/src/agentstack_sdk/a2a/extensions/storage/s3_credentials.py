# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pydantic import field_serializer
from pydantic_core.core_schema import SerializationInfo

from agentstack_sdk.a2a.extensions.base import (
    BaseExtensionClient,
    BaseExtensionServer,
    NoParamsBaseExtensionSpec,
)
from agentstack_sdk.a2a.extensions.exceptions import ExtensionError
from agentstack_sdk.a2a.extensions.storage.s3 import S3Config
from agentstack_sdk.util.pydantic import REVEAL_SECRETS, SecureBaseModel, redact_str

__all__ = [
    "S3_CREDENTIALS_EXTENSION_URI",
    "S3CredentialsExtensionClient",
    "S3CredentialsExtensionMetadata",
    "S3CredentialsExtensionServer",
    "S3CredentialsExtensionSpec",
]

S3_CREDENTIALS_EXTENSION_URI = "https://a2a-extensions.agentstack.beeai.dev/storage/s3-credentials/v1"


class S3CredentialsExtensionMetadata(SecureBaseModel):
    """STS-style credential bundle passed from client → agent."""

    endpoint: str
    """S3-compatible endpoint URL."""

    bucket: str
    """Target S3 bucket."""

    access_key_id: str
    """AWS / MinIO access key ID."""

    secret_access_key: str
    """AWS / MinIO secret access key."""

    session_token: str | None = None
    """STS session token; None for non-STS (demo)."""

    region: str = "us-east-1"
    use_ssl: bool = False

    prefix: str = ""
    """IAM-scoped key prefix, e.g. 'contexts/{context_id}/'."""

    ttl: int = 3600
    """Presigned GET URL TTL in seconds."""

    @field_serializer("access_key_id", "secret_access_key")
    @classmethod
    def _redact_key(cls, v: str, info: SerializationInfo) -> str:
        return redact_str(v, info)

    @field_serializer("session_token")
    @classmethod
    def _redact_token(cls, v: str | None, info: SerializationInfo) -> str | None:
        return redact_str(v, info) if v is not None else None


class S3CredentialsExtensionSpec(NoParamsBaseExtensionSpec):
    URI = S3_CREDENTIALS_EXTENSION_URI


class S3CredentialsExtensionServer(BaseExtensionServer[S3CredentialsExtensionSpec, S3CredentialsExtensionMetadata]):
    """
    Agent-side handler. Uses injected STS-style credentials to upload/download
    objects directly via aioboto3. Returns presigned GET URLs so receivers never
    need an S3 SDK.
    """

    async def upload(self, filename: str, content: bytes, content_type: str = "application/octet-stream") -> str:
        """PUT content at {prefix}{filename} and return a presigned GET URL."""
        if not self.data:
            raise ExtensionError(self.spec, "S3 credentials extension metadata was not provided")

        try:
            import aioboto3
        except ImportError as e:
            raise ImportError(
                "aioboto3 is required for S3CredentialsExtensionServer. "
                "Install it with: pip install 'agentstack-sdk[s3]'"
            ) from e

        from botocore.config import Config

        creds = self.data
        key = f"{creds.prefix}{filename}"
        session = aioboto3.Session()
        async with session.client(
            "s3",
            endpoint_url=creds.endpoint,
            aws_access_key_id=creds.access_key_id,
            aws_secret_access_key=creds.secret_access_key,
            aws_session_token=creds.session_token,
            region_name=creds.region,
            use_ssl=creds.use_ssl,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        ) as s3:
            await s3.put_object(Bucket=creds.bucket, Key=key, Body=content, ContentType=content_type)
            download_url = await s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": creds.bucket, "Key": key},
                ExpiresIn=creds.ttl,
            )
        return download_url

    async def download(self, key: str) -> bytes:
        """GET object at {prefix}{key} using injected credentials."""
        if not self.data:
            raise ExtensionError(self.spec, "S3 credentials extension metadata was not provided")

        try:
            import aioboto3
        except ImportError as e:
            raise ImportError(
                "aioboto3 is required for S3CredentialsExtensionServer. "
                "Install it with: pip install 'agentstack-sdk[s3]'"
            ) from e

        from botocore.config import Config

        creds = self.data
        full_key = f"{creds.prefix}{key}"
        session = aioboto3.Session()
        async with session.client(
            "s3",
            endpoint_url=creds.endpoint,
            aws_access_key_id=creds.access_key_id,
            aws_secret_access_key=creds.secret_access_key,
            aws_session_token=creds.session_token,
            region_name=creds.region,
            use_ssl=creds.use_ssl,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        ) as s3:
            resp = await s3.get_object(Bucket=creds.bucket, Key=full_key)
            return await resp["Body"].read()


class S3CredentialsExtensionClient(BaseExtensionClient[S3CredentialsExtensionSpec, None]):
    """
    Client-side helper. Serializes STS-style credentials + prefix into message
    metadata so the agent can upload freely within the scoped prefix.

    Demo usage (plain long-lived credentials, no STS):

        client = S3CredentialsExtensionClient(config=s3_config, context_id=ctx_id)
        metadata = client.metadata()

    Production usage (short-lived STS credentials, IAM-scoped to the context prefix):

        client = await S3CredentialsExtensionClient.from_sts(
            role_arn="arn:aws:iam::123456789012:role/AgentUploadRole",
            context_id=ctx_id,
            endpoint="https://s3.amazonaws.com",
            bucket="my-bucket",
            region="us-east-1",
            ttl=3600,
        )
        metadata = client.metadata()
    """

    def __init__(
        self,
        config: S3Config,
        context_id: str,
        *,
        session_token: str | None = None,
        spec: S3CredentialsExtensionSpec | None = None,
    ) -> None:
        super().__init__(spec or S3CredentialsExtensionSpec())
        self._config = config
        self._prefix = f"contexts/{context_id}/"
        self._session_token = session_token

    @classmethod
    async def from_sts(
        cls,
        *,
        role_arn: str,
        context_id: str,
        endpoint: str,
        bucket: str,
        region: str = "us-east-1",
        use_ssl: bool = True,
        ttl: int = 3600,
        spec: S3CredentialsExtensionSpec | None = None,
    ) -> "S3CredentialsExtensionClient":
        """
        Obtain short-lived credentials via AWS STS AssumeRole with an inline
        policy scoped to ``contexts/{context_id}/*``, then construct the client.

        The resulting session token is wired through to the agent so that IAM
        enforces the namespace isolation at the infrastructure level — no
        application-level key prefix check is needed.

        Requires the caller's IAM identity to have ``sts:AssumeRole`` permission
        on *role_arn*.  The role's trust policy must allow that identity.

        Example IAM inline policy attached to the assumed role session::

            {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Action": ["s3:PutObject", "s3:GetObject", "s3:ListObjectsV2"],
                    "Resource": "arn:aws:s3:::<bucket>/contexts/<context_id>/*"
                }]
            }
        """
        import json

        try:
            import aioboto3
        except ImportError as e:
            raise ImportError(
                "aioboto3 is required for S3CredentialsExtensionClient.from_sts. "
                "Install it with: pip install 'agentstack-sdk[s3]'"
            ) from e

        scoped_policy = json.dumps({
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": ["s3:PutObject", "s3:GetObject", "s3:ListObjectsV2"],
                "Resource": f"arn:aws:s3:::{bucket}/contexts/{context_id}/*",
            }],
        })

        session = aioboto3.Session()
        async with session.client("sts", region_name=region) as sts:
            response = await sts.assume_role(
                RoleArn=role_arn,
                RoleSessionName=f"agent-{context_id[:16]}",
                Policy=scoped_policy,
                DurationSeconds=ttl,
            )

        creds = response["Credentials"]
        config = S3Config(
            endpoint_url=endpoint,
            bucket=bucket,
            access_key=creds["AccessKeyId"],
            secret_key=creds["SecretAccessKey"],
            region=region,
            use_ssl=use_ssl,
        )
        return cls(config=config, context_id=context_id, session_token=creds["SessionToken"], spec=spec)

    def metadata(self, ttl: int = 3600) -> dict:
        """Serialize credentials + prefix into message metadata."""
        return {
            S3_CREDENTIALS_EXTENSION_URI: S3CredentialsExtensionMetadata(
                endpoint=self._config.endpoint_url,
                bucket=self._config.bucket,
                access_key_id=self._config.access_key.get_secret_value(),
                secret_access_key=self._config.secret_key.get_secret_value(),
                session_token=self._session_token,
                region=self._config.region,
                use_ssl=self._config.use_ssl,
                prefix=self._prefix,
                ttl=ttl,
            ).model_dump(mode="json", context={REVEAL_SECRETS: True})
        }
