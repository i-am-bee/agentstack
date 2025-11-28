# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import contextvars
import json
import logging
import traceback
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from types import NoneType
from typing import Any

import pydantic

from agentstack_sdk.a2a.extensions.base import (
    BaseExtensionClient,
    BaseExtensionServer,
    BaseExtensionSpec,
)
from agentstack_sdk.a2a.types import AgentMessage, JsonDict, Metadata

logger = logging.getLogger(__name__)


class Error(pydantic.BaseModel):
    """
    Represents error information for displaying exceptions in the UI.

    This extension helps display errors in a user-friendly way with:
    - A clear error title (exception type)
    - A descriptive error message

    Visually, this may appear as an error card in the UI.

    Properties:
    - title: Title of the error (typically the exception class name).
    - message: The error message describing what went wrong.
    """

    title: str
    message: str


class ErrorGroup(pydantic.BaseModel):
    """
    Represents a group of errors.

    Properties:
    - message: A message describing the group of errors.
    - errors: A list of error objects.
    """

    message: str
    errors: list[Error]


class ErrorMetadata(pydantic.BaseModel):
    """
    Metadata containing an error (or group of errors) and an optional stack trace.

    Properties:
    - error: The error object or group of errors.
    - stack_trace: Optional formatted stack trace for debugging.
    - context: Optional context dictionary.
    """

    error: Error | ErrorGroup
    stack_trace: str | None = None
    context: JsonDict | None = None


class ErrorExtensionParams(pydantic.BaseModel):
    """
    Configuration parameters for the error extension.

    Properties:
    - include_stacktrace: Whether to include stack traces in error messages (default: False).
    """

    include_stacktrace: bool = False


class ErrorExtensionSpec(BaseExtensionSpec[ErrorExtensionParams]):
    URI: str = "https://a2a-extensions.agentstack.beeai.dev/ui/error/v1"


def _format_stacktrace(exc: BaseException, include_cause: bool = True) -> str:
    """Format exception with full traceback including nested causes."""
    return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__, chain=include_cause))


def _extract_error(exc: BaseException) -> Error | ErrorGroup:
    """
    Extract error information from an exception, handling:
    - BaseExceptionGroup (returns ErrorGroup)
    - FrameworkError from beeai_framework (uses .explain() method)
    """
    # Handle BaseExceptionGroup by recursively extracting errors from each exception
    if isinstance(exc, BaseExceptionGroup):
        errors: list[Error] = []
        for sub_exc in exc.exceptions:
            extracted = _extract_error(sub_exc)
            if isinstance(extracted, ErrorGroup):
                errors.extend(extracted.errors)
            else:
                errors.append(extracted)
        return ErrorGroup(message=str(exc), errors=errors)

    # Try to handle FrameworkError if beeai_framework is available
    try:
        from beeai_framework.errors import FrameworkError

        if isinstance(exc, FrameworkError):
            # FrameworkError has special .explain() method
            return Error(title=exc.name(), message=exc.explain())
    except ImportError:
        # beeai_framework not installed, continue with standard handling
        pass

    return Error(title=type(exc).__name__, message=str(exc))


class ErrorExtensionServer(BaseExtensionServer[ErrorExtensionSpec, NoneType]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Server-scoped ContextVar for request-scoped error context
        self._error_context_var: contextvars.ContextVar[JsonDict] = contextvars.ContextVar("error_context")

    @asynccontextmanager
    async def lifespan(self) -> AsyncIterator[None]:
        """Set up request-scoped error context using ContextVar."""
        # Set an empty dict for this request's context
        token = self._error_context_var.set({})

        try:
            yield
        finally:
            self._error_context_var.reset(token)

    @property
    def context(self) -> JsonDict:
        """Get the current request's error context."""
        try:
            return self._error_context_var.get()
        except LookupError:
            # Fallback for when lifespan hasn't been entered yet
            logger.warning(
                "Attempted to use error context when the error extension is not initialized. Make sure to add the ErrorExtensionServer to the agent dependencies."
            )
            return {}

    def error_metadata(self, error: BaseException) -> Metadata[str, Any]:
        """
        Create metadata for an error.

        Args:
            error: The exception to convert to metadata

        Returns:
            Metadata dictionary with error information
        """
        error_data = _extract_error(error)
        stack_trace = _format_stacktrace(error) if self.spec.params.include_stacktrace else None
        return Metadata(
            {
                self.spec.URI: ErrorMetadata(
                    error=error_data,
                    stack_trace=stack_trace,
                    context=self.context or None,
                ).model_dump(mode="json")
            }
        )

    def message(
        self,
        error: BaseException,
    ) -> AgentMessage:
        """
        Create an AgentMessage with error metadata and serialized text representation.

        Args:
            error: The exception to include in the message

        Returns:
            AgentMessage with error metadata and markdown-formatted text
        """
        metadata = self.error_metadata(error)
        error_metadata = ErrorMetadata.model_validate(metadata[self.spec.URI])

        # Serialize to markdown for display
        text_lines: list[str] = []
        if isinstance(error_metadata.error, ErrorGroup):
            text_lines.append(f"## {error_metadata.error.message}\n")
            for err in error_metadata.error.errors:
                text_lines.append(f"### {err.title}\n{err.message}")
        else:
            text_lines.append(f"## {error_metadata.error.title}\n{error_metadata.error.message}")

        # Add context if present
        if error_metadata.context:
            text_lines.append(f"## Context\n```json\n{json.dumps(error_metadata.context, indent=2)}\n```")

        if error_metadata.stack_trace:
            text_lines.append(f"## Stack Trace\n```\n{error_metadata.stack_trace}\n```")

        text = "\n\n".join(text_lines)

        return AgentMessage(text=text, metadata=metadata)


class ErrorExtensionClient(BaseExtensionClient[ErrorExtensionSpec, ErrorMetadata]): ...
