# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import inspect
from typing import Annotated, TypedDict, Unpack

import pytest

from agentstack_sdk.a2a.extensions import CitationExtensionServer, CitationExtensionSpec
from agentstack_sdk.server.dependencies import extract_dependencies


@pytest.mark.unit
def test_extract_dependencies_simple() -> None:
    def agent(a: Annotated[CitationExtensionServer, CitationExtensionSpec()]) -> None:
        pass

    signature = inspect.signature(agent)
    assert extract_dependencies(signature).keys() == {"a"}


@pytest.mark.unit
def test_extract_dependencies_extra_parameters() -> None:
    def agent(a: Annotated[CitationExtensionServer, CitationExtensionSpec()], b: bool) -> None:
        pass

    signature = inspect.signature(agent)
    with pytest.raises(TypeError) as exc_info:
        extract_dependencies(signature)

    assert str(exc_info.value) == "The agent function contains extra parameters with unknown type annotation: {'b'}"


@pytest.mark.unit
def test_extract_dependencies_kwargs() -> None:
    class MyExtensions(TypedDict):
        a: Annotated[CitationExtensionServer, CitationExtensionSpec()]
        b: Annotated[CitationExtensionServer, CitationExtensionSpec()]
        c: Annotated[CitationExtensionServer, CitationExtensionSpec()]

    def agent(**kwargs: Unpack[MyExtensions]) -> None:
        pass

    signature = inspect.signature(agent)
    assert extract_dependencies(signature).keys() == {"a", "b", "c"}


@pytest.mark.unit
def test_extract_dependencies_complex() -> None:
    class MyExtensions(TypedDict):
        b: Annotated[CitationExtensionServer, CitationExtensionSpec()]

    def agent(
        a: Annotated[CitationExtensionServer, CitationExtensionSpec()],
        **kwargs: Unpack[MyExtensions],
    ) -> None:
        pass

    signature = inspect.signature(agent)
    assert extract_dependencies(signature).keys() == {"a", "b"}
