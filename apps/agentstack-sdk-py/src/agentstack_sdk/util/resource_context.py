# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import contextlib
import contextvars
import typing


async def noop():
    pass


P = typing.ParamSpec("P")
T = typing.TypeVar("T")


def resource_context(
    factory: typing.Callable[P, T],
    default_factory: typing.Callable[[], T],
) -> tuple[typing.Callable[[], T], typing.Callable[P, contextlib.AbstractContextManager[T]]]:
    contextvar: contextvars.ContextVar[T] = contextvars.ContextVar(f"resource_context({factory.__name__})")

    def use_resource(*args: P.args, **kwargs: P.kwargs):
        @contextlib.contextmanager
        def manager():
            resource = factory(*args, **kwargs)
            token = contextvar.set(resource)
            try:
                yield resource
            finally:
                contextvar.reset(token)

        return manager()

    def get_resource() -> T:
        try:
            return contextvar.get()
        except LookupError:
            return default_factory()

    return get_resource, use_resource


__all__ = ["resource_context"]
