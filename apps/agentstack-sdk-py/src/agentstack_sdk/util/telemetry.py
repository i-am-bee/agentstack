# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

# Modified version of https://github.com/a2aproject/a2a-python/blob/2acd838796d44ab9bfe6ba8c8b4ea0c2571a59dc/src/a2a/utils/telemetry.py

import asyncio
import functools
import inspect
import logging
from collections.abc import Callable, Iterable, Mapping
from typing import Any

from opentelemetry import trace
from opentelemetry.trace import SpanKind, StatusCode

from agentstack_sdk import __version__

INSTRUMENTING_MODULE_NAME = "agentstack-python-sdk"
INSTRUMENTING_MODULE_VERSION = __version__

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(INSTRUMENTING_MODULE_NAME, INSTRUMENTING_MODULE_VERSION)


def trace_function(
    func: Callable | None = None,
    *,
    span_name: str | None = None,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: dict[str, Any] | None = None,
    attribute_extractor: Callable | None = None,
) -> Callable:
    """A decorator to automatically trace a function call with OpenTelemetry.

    This decorator can be used to wrap both sync and async functions.
    When applied, it creates a new span for each call to the decorated function.
    The span will record the execution time, status (OK or ERROR), and any
    exceptions that occur.

    It can be used in two ways:

    1. As a direct decorator: `@trace_function`
    2. As a decorator factory to provide arguments: `@trace_function(span_name="custom.name")`

    Args:
        func (callable, optional): The function to be decorated. If None,
            the decorator returns a partial function, allowing it to be called
            with arguments. Defaults to None.
        span_name (str, optional): Custom name for the span. If None,
            it defaults to ``f'{func.__module__}.{func.__name__}'``.
            Defaults to None.
        kind (SpanKind, optional): The ``opentelemetry.trace.SpanKind`` for the
            created span. Defaults to ``SpanKind.INTERNAL``.
        attributes (dict, optional): A dictionary of static attributes to be
            set on the span. Keys are attribute names (str) and values are
            the corresponding attribute values. Defaults to None.
        attribute_extractor (callable, optional): A function that can be used
            to dynamically extract and set attributes on the span.
            It is called within a ``finally`` block, ensuring it runs even if
            the decorated function raises an exception.
            The function signature should be:
            ``attribute_extractor(span, args, kwargs, result, exception)``
            where:
                - ``span`` : the OpenTelemetry ``Span`` object.
                - ``args`` : a tuple of positional arguments passed
                - ``kwargs`` : a dictionary of keyword arguments passed
                - ``result`` : return value (None if an exception occurred)
                - ``exception`` : exception object if raised (None otherwise).
            Any exception raised by the ``attribute_extractor`` itself will be
            caught and logged. Defaults to None.

    Returns:
        callable: The wrapped function that includes tracing, or a partial
            decorator if ``func`` is None.
    """
    if func is None:
        return functools.partial(
            trace_function,
            span_name=span_name,
            kind=kind,
            attributes=attributes,
            attribute_extractor=attribute_extractor,
        )

    actual_span_name = span_name or f"{func.__module__}.{func.__name__}"

    is_async_func = inspect.iscoroutinefunction(func)

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs) -> Any:
        """Async Wrapper for the decorator."""
        with tracer.start_as_current_span(actual_span_name, kind=kind) as span:
            if attributes:
                for k, v in attributes.items():
                    span.set_attribute(k, v)

            result = None
            exception = None

            try:
                # Async wrapper, await for the function call to complete.
                result = await func(*args, **kwargs)  # pyrefly: ignore[not-callable]
                span.set_status(StatusCode.OK)
            # asyncio.CancelledError extends from BaseException
            except asyncio.CancelledError as ce:
                exception = None
                span.record_exception(ce)
                raise
            except Exception as e:
                exception = e
                span.record_exception(e)
                span.set_status(StatusCode.ERROR, description=str(e))
                raise
            finally:
                if attribute_extractor:
                    try:
                        attribute_extractor(span, args, kwargs, result, exception)
                    except Exception:
                        logger.exception(
                            "attribute_extractor error in span %s",
                            actual_span_name,
                        )
            return result

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs) -> Any:
        """Sync Wrapper for the decorator."""
        with tracer.start_as_current_span(actual_span_name, kind=kind) as span:
            if attributes:
                for k, v in attributes.items():
                    span.set_attribute(k, v)

            result = None
            exception = None

            try:
                # Sync wrapper, execute the function call.
                result = func(*args, **kwargs)  # pyrefly: ignore[not-callable]
                span.set_status(StatusCode.OK)

            except Exception as e:
                exception = e
                span.record_exception(e)
                span.set_status(StatusCode.ERROR, description=str(e))
                raise
            finally:
                if attribute_extractor:
                    try:
                        attribute_extractor(span, args, kwargs, result, exception)
                    except Exception:
                        logger.exception(
                            "attribute_extractor error in span %s",
                            actual_span_name,
                        )
            return result

    return async_wrapper if is_async_func else sync_wrapper


def trace_class(
    include_list: list[str] | None = None,
    exclude_list: list[str] | None = None,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: dict[str, Any] | None = None,
) -> Callable:
    """A class decorator to automatically trace specified methods of a class.

    This decorator iterates over the methods of a class and applies the
    `trace_function` decorator to them, based on the `include_list` and
    `exclude_list` criteria. Methods starting or ending with double underscores
    (dunder methods, e.g., `__init__`, `__call__`) are always excluded by default.

    Args:
        include_list (list[str], optional): A list of method names to
            explicitly include for tracing. If provided, only methods in this
            list (that are not dunder methods) will be traced.
            Defaults to None (trace all non-dunder methods).
        exclude_list (list[str], optional): A list of method names to exclude
            from tracing. This is only considered if `include_list` is not
            provided. Dunder methods are implicitly excluded.
            Defaults to an empty list.
        kind (SpanKind, optional): The `opentelemetry.trace.SpanKind` for the
            created spans on the methods. Defaults to `SpanKind.INTERNAL`.

    Returns:
        callable: A decorator function that, when applied to a class,
                  modifies the class to wrap its specified methods with tracing.

    Example:
        To trace all methods except 'internal_method':
        ```python
        @trace_class(exclude_list=['internal_method'])
        class MyService:
            def public_api(self):
                pass

            def internal_method(self):
                pass
        ```

        To trace only 'method_one' and 'method_two':
        ```python
        @trace_class(include_list=['method_one', 'method_two'])
        class AnotherService:
            def method_one(self):
                pass

            def method_two(self):
                pass

            def not_traced_method(self):
                pass
        ```
    """
    exclude_list = exclude_list or []

    def decorator(cls: Any) -> Any:
        for name, method in inspect.getmembers(cls, inspect.isfunction):
            if name.startswith("__") and name.endswith("__"):
                continue
            if include_list and name not in include_list:
                continue
            if not include_list and name in exclude_list:
                continue

            span_name = f"{cls.__module__}.{cls.__name__}.{name}"
            setattr(
                cls,
                name,
                trace_function(span_name=span_name, kind=kind, attributes=attributes)(method),
            )
        return cls

    return decorator


def flatten_dict(
    d: Mapping[str, Any],
    parent_key: str = "",
    sep: str = ".",
    skip_none: bool = True,
    max_depth: int | None = None,
) -> dict[str, Any]:
    """
    Flatten nested dict → OpenTelemetry-compatible flat dict.

    - Lists are usually kept as-is (OTel supports primitive arrays)
    - None values are skipped by default
    """
    items: list[tuple[str, Any]] = []

    current_depth = parent_key.count(sep) + 1 if parent_key else 0
    if max_depth is not None and current_depth > max_depth:
        # Optional: prevent runaway depth
        items.append((parent_key, "[max depth exceeded]"))
        return dict(items)

    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k

        if skip_none and v is None:
            continue

        if isinstance(v, Mapping):
            items.extend(flatten_dict(v, new_key, sep, skip_none, max_depth).items())

        elif isinstance(v, (str, bool, int, float, type(None))):
            items.append((new_key, v))

        elif isinstance(v, Iterable) and not isinstance(v, (str, bytes)):
            # Keep lists/arrays as-is — OpenTelemetry supports them
            items.append((new_key, list(v)))  # make sure it's a list

        else:
            # Fallback: convert unknown types to string
            items.append((new_key, str(v)))

    return dict(items)
