# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import inspect
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from inspect import isclass
from typing import Annotated, Any, Generic, get_args, get_origin

import fastapi
from a2a.types import Message
from typing_extensions import Doc

from beeai_sdk.a2a.extensions import BaseExtensionSpec
from beeai_sdk.a2a.extensions.base import BaseExtensionServer, ExtensionSpecT, MetadataFromClientT
from beeai_sdk.server.context import RunContext

fastapi.Depends()


# Inspired by fastapi.Depends
class Depends(Generic[ExtensionSpecT, MetadataFromClientT]):
    extension: BaseExtensionServer[ExtensionSpecT, MetadataFromClientT] | None = None

    def __init__(
        self,
        dependency: Annotated[
            Callable[[Message, RunContext], Any] | BaseExtensionServer[ExtensionSpecT, MetadataFromClientT],
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

    def __call__(self, message: Message, context: RunContext) -> Any:
        return self._dependency_callable(message, context)

    @asynccontextmanager
    async def lifespan(self) -> AsyncIterator[None]:
        if self.extension:
            async with self.extension.lifespan():
                yield
        else:
            yield


def extract_dependencies(sign: inspect.Signature) -> dict[str, Depends]:
    dependencies = {}
    for name, param in sign.parameters.items():
        if get_origin(param.annotation) is Annotated:
            args = get_args(param.annotation)
            if len(args) > 1:
                dep_type, spec, *_ = args
                # extension_param: Annotated[some_type, Depends(some_callable)]
                if isinstance(spec, Depends):
                    dependencies[name] = spec
                # extension_param: Annotated[BaseExtensionServer, BaseExtensionSpec()]
                elif (
                    isclass(dep_type)
                    and issubclass(dep_type, BaseExtensionServer)
                    and isinstance(spec, BaseExtensionSpec)
                ):
                    dependencies[name] = Depends(dep_type(spec))

        elif inspect.isclass(param.annotation):
            # message: Message
            if param.annotation == Message:
                dependencies[name] = Depends(lambda message, _context: message)
            # context: Context
            elif param.annotation == RunContext:
                dependencies[name] = Depends(lambda _message, context: context)
            # extension: BaseExtensionServer = BaseExtensionSpec()
            # TODO: this does not get past linters, should we enable it or somehow fix the typing?
            # elif issubclass(param.annotation, BaseExtensionServer) and isinstance(param.default, BaseExtensionSpec):
            #     dependencies[name] = Depends(param.annotation(param.default))

    if extra_parameters := sign.parameters.keys() - dependencies.keys():
        raise TypeError(
            f"The agent function contains extra parameters with unknown type annotation: {extra_parameters}"
        )

    return dependencies
