# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Any

from pydantic import AnyUrl, BaseModel, Secret, SecretBytes, SecretStr, field_serializer
from pydantic_core.core_schema import SerializationInfo

REVEAL_SECRETS = "reveal_secrets"
REDACT_SECRETS = "redact_secrets"

_REDACTED = "***redacted***"


class SecureBaseModel(BaseModel):
    """
    Base class that automatically handles SecretStr redaction unless explicitly revealed via context.
    Inherit from this instead of BaseModel for models that may contain secrets.
    """

    @field_serializer("*")
    @classmethod
    def _redact_secrets(cls, v: Any, info: SerializationInfo) -> Any:
        if isinstance(v, (Secret, SecretStr, SecretBytes)):
            return redact_secret(v, info)
        elif isinstance(v, AnyUrl):
            return redact_url(v, info)
        return v


def should_reveal(info: SerializationInfo) -> bool:
    return bool(info.context and info.context.get(REVEAL_SECRETS, False))


def should_redact(info: SerializationInfo) -> bool:
    return bool(info.context and info.context.get(REDACT_SECRETS, False))


def redact_secret(
    v: Secret | SecretStr | SecretBytes, info: SerializationInfo
) -> Secret | SecretStr | SecretBytes | str | bytes:
    if should_redact(info):
        return _REDACTED
    elif should_reveal(info):
        return v.get_secret_value()
    else:
        return v


def redact_str(v: str, info: SerializationInfo) -> str:
    return _REDACTED if should_redact(info) else v


def redact_url(v: AnyUrl, info: SerializationInfo) -> AnyUrl:
    return (
        AnyUrl.build(
            scheme=v.scheme,
            username=_REDACTED if v.username else None,
            password=_REDACTED if v.password else None,
            host=v.host or "",
            path=v.path.lstrip("/") if v.path else None,
            port=v.port,
            query=_REDACTED if v.query else None,
            fragment=_REDACTED if v.fragment else None,
        )
        if should_redact(info)
        else v
    )


def redact_dict(v: dict[str, str], info: SerializationInfo) -> dict[str, str]:
    return {k: redact_str(val, info) for k, val in v.items()} if should_redact(info) else v
