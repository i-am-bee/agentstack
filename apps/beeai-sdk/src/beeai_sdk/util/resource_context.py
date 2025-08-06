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
    resource_factory: typing.Callable[P, T],
    default_resource_factory: typing.Callable[[], T],
) -> tuple[typing.Callable[[], T], typing.Callable[P, contextlib.AbstractAsyncContextManager[T]]]:
    contextvar: contextvars.ContextVar[T] = contextvars.ContextVar(f"resource_context({resource_factory.__name__})")

    def with_resource(*args: P.args, **kwargs: P.kwargs):
        @contextlib.asynccontextmanager
        async def manager():
            resource = resource_factory(*args, **kwargs)
            token = contextvar.set(resource)
            try:
                yield resource
            finally:
                _ = await getattr(resource, "aclose", noop)()
                contextvar.reset(token)

        return manager()

    def get_resource() -> T:
        try:
            return contextvar.get()
        except LookupError:
            return default_resource_factory()

    return get_resource, with_resource


__all__ = ["resource_context"]
