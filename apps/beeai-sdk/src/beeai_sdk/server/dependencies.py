# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import inspect
from collections import Counter
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from inspect import isclass
from typing import Annotated, Any, Generic, TypeAlias, Unpack, get_args, get_origin

from a2a.types import Message
from typing_extensions import Doc

from beeai_sdk.a2a.extensions import BaseExtensionSpec
from beeai_sdk.a2a.extensions.base import (
    BaseExtensionServer,
    ExtensionSpecT,
    MetadataFromClientT,
)
from beeai_sdk.server.context import RunContext

Dependency: TypeAlias = (
    Callable[[Message, RunContext, dict], Any]
    | BaseExtensionServer[ExtensionSpecT, MetadataFromClientT]
)


# Inspired by fastapi.Depends
class Depends(Generic[ExtensionSpecT, MetadataFromClientT]):
    extension: BaseExtensionServer[ExtensionSpecT, MetadataFromClientT] | None = None

    def __init__(
        self,
        dependency: Annotated[
            Dependency,
            Doc(
                """
                A "dependable" callable (like a function).
                Don't call it directly, BeeAI SDK will call it for you, just pass the object directly.
                """
            ),
        ],
    ):
        self._dependency_callable = dependency
        if isinstance(dependency, BaseExtensionServer):
            self.extension = dependency

    def __call__(
        self, message: Message, context: RunContext, dependencies: dict[str, Any]
    ) -> AbstractAsyncContextManager[Any]:
        instance = self._dependency_callable(message, context, dependencies)

        @asynccontextmanager
        async def lifespan() -> AsyncIterator[Any]:
            if self.extension or hasattr(instance, "lifespan"):
                async with instance.lifespan():
                    yield instance
            else:
                yield instance

        return lifespan()


def extract_dependencies(sign: inspect.Signature) -> dict[str, Depends]:
    dependencies = {}
    seen_keys = set()

    def process_args(name: str, args: tuple[Any, ...]) -> None:
        if len(args) > 1:
            dep_type, spec, *rest = args
            # extension_param: Annotated[some_type, Depends(some_callable)]
            if isinstance(spec, Depends):
                dependencies[name] = spec
            # extension_param: Annotated[BaseExtensionServer, BaseExtensionSpec()]
            elif (
                isclass(dep_type)
                and issubclass(dep_type, BaseExtensionServer)
                and isinstance(spec, BaseExtensionSpec)
            ):
                dependencies[name] = Depends(dep_type(spec, *rest))

    for name, param in sign.parameters.items():
        seen_keys.add(name)

        if get_origin(param.annotation) is Annotated:
            args = get_args(param.annotation)
            process_args(name, args)

        elif inspect.isclass(param.annotation):
            # message: Message
            if param.annotation == Message:
                dependencies[name] = Depends(
                    lambda message, _context, _dependencies: message
                )
            # context: Context
            elif param.annotation == RunContext:
                dependencies[name] = Depends(
                    lambda _message, context, _dependencies: context
                )
            # extension: BaseExtensionServer = BaseExtensionSpec()
            # TODO: this does not get past linters, should we enable it or somehow fix the typing?
            # elif issubclass(param.annotation, BaseExtensionServer) and isinstance(param.default, BaseExtensionSpec):
            #     dependencies[name] = Depends(param.annotation(param.default))
        elif param.kind is inspect.Parameter.VAR_KEYWORD:
            origin = get_origin(param.annotation)
            if origin is Unpack:
                seen_keys.discard(name)
                (typed_dict,) = get_args(param.annotation)
                for field_name, field_type in typed_dict.__annotations__.items():
                    seen_keys.add(field_name)
                    if get_origin(field_type) is Annotated:
                        args = get_args(field_type)
                        process_args(field_name, args)

    missing_keys = seen_keys.difference(dependencies.keys())
    if missing_keys:
        raise TypeError(
            f"The agent function contains extra parameters with unknown type annotation: {missing_keys}"
        )
    if reserved_names := {param for param in dependencies if param.startswith("__")}:
        raise TypeError(
            f"User-defined dependencies cannot start with double underscore: {reserved_names}"
        )

    extension_deps = Counter(
        dep.extension.spec.URI for dep in dependencies.values() if dep.extension
    )
    if duplicate_uris := {k for k, v in extension_deps.items() if v > 1}:
        raise TypeError(
            f"Duplicate extension URIs found in the agent function: {duplicate_uris}"
        )

    return dependencies
