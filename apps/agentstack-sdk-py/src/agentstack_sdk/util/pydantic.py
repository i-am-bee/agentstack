# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

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


def apply_compatibility_monkey_patching():
    """
    Workaround for Pydantic + Python 3.14 issue where TypeAdapter[ChatModelKwargs] is not fully defined.
    This happens because TypedDict annotations are deferred in 3.14 and Pydantic's lazy build fails to resolve them.
    """
    import sys
    from contextlib import suppress

    # Fix for Python 3.14 + Pydantic 2.12.x + prefer_fwd_module TypeError
    if sys.version_info >= (3, 14):
        import typing
        with suppress(ImportError, AttributeError):
            import pydantic._internal._typing_extra as typing_extra

            if hasattr(typing_extra, "_eval_type"):
                def patched_eval_type(value, globalns=None, localns=None, type_params=None):
                    # Python 3.14 typing._eval_type doesn't support prefer_fwd_module
                    # but Pydantic 2.12.x incorrectly passes it.
                    evaluated = typing._eval_type(value, globalns, localns, type_params=type_params)
                    if evaluated is None:
                        evaluated = type(None)
                    return evaluated

                typing_extra._eval_type = patched_eval_type

    with suppress(ImportError):
        from beeai_framework.context import RunContext, RunMiddlewareType  # noqa: F401
        from pydantic import BaseModel, TypeAdapter

        # Fix ChatModelKwargs
        with suppress(ImportError, AttributeError):
            import beeai_framework.backend.chat as chat_module

            try:
                chat_module._ChatModelKwargsAdapter.validate_python({})
            except Exception:
                class _ChatModelKwargsRebuilder(BaseModel):
                    kwargs: chat_module.ChatModelKwargs

                _ChatModelKwargsRebuilder.model_rebuild()
                # Re-create the adapter with explicit module to ensure forward references are resolved
                chat_module._ChatModelKwargsAdapter = TypeAdapter(chat_module.ChatModelKwargs, module=chat_module.__name__)

        # Fix EmbeddingModelKwargs
        with suppress(ImportError, AttributeError):
            import beeai_framework.backend.embedding as embedding_module

            try:
                embedding_module._EmbeddingModelKwargsAdapter.validate_python({})
            except Exception:
                class _EmbeddingModelKwargsRebuilder(BaseModel):
                    kwargs: embedding_module.EmbeddingModelKwargs

                _EmbeddingModelKwargsRebuilder.model_rebuild()
                # Re-create the adapter with explicit module to ensure forward references are resolved
                embedding_module._EmbeddingModelKwargsAdapter = TypeAdapter(
                    embedding_module.EmbeddingModelKwargs, module=embedding_module.__name__
                )
